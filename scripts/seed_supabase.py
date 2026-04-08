#!/usr/bin/env python3
"""Seed Supabase cloud DB with realistic test data for thesis screenshots.

Usage:
    DATABASE_URL="postgresql+asyncpg://..." python scripts/seed_supabase.py
"""

import asyncio
import json
import os
import random
import sys
import unicodedata
from datetime import date, time, timedelta
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.core.security import hash_password

uid = lambda: str(uuid4())
today = date.today()


def normalize_specialty_key(name: str) -> str:
    """Strip accents, lowercase, replace spaces with hyphens.

    Mirrors `normalize_specialty_name` in
    `app/modules/medical_records/infrastructure/repositories/sqlalchemy_form_schema_repository.py`.
    """
    nfkd = unicodedata.normalize("NFKD", name.lower())
    ascii_text = nfkd.encode("ascii", "ignore").decode("ascii")
    return ascii_text.replace(" ", "-").replace("(", "").replace(")", "")


async def q(s, sql, p=None):
    """Execute raw SQL, skip on duplicate key."""
    try:
        return await s.execute(text(sql), p or {})
    except Exception as e:
        msg = str(e).lower()
        if any(k in msg for k in ("duplicate", "unique", "conflict")):
            await s.rollback()
            return None
        raise


async def fetch_scalar(s, sql, p=None):
    r = await s.execute(text(sql), p or {})
    return r.scalar()


async def main():
    db_url = os.environ.get("DATABASE_URL", get_settings().DATABASE_URL)
    engine = create_async_engine(db_url)
    S = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with S() as s:
        print("Seeding Supabase...\n")

        # ── 1. Roles ─────────────────────────────────────────────
        roles = {}
        for name in ["admin", "doctor", "analista", "farmacia", "paciente"]:
            row = await fetch_scalar(s, "SELECT id FROM roles WHERE name = :n", {"n": name})
            if row:
                roles[name] = row
            else:
                rid = uid()
                await q(s, "INSERT INTO roles (id, name) VALUES (:id, :n)", {"id": rid, "n": name})
                roles[name] = rid
        await s.commit()
        print(f"  Roles: {len(roles)}")

        # ── 1b. Permissions + role_permissions ──────────────────
        # Catalog of permission codes (mirrors permission_seeder.py)
        permission_defs = [
            ("patients:read",        "patients",     "Listar y ver pacientes"),
            ("patients:create",      "patients",     "Crear pacientes"),
            ("patients:update",      "patients",     "Actualizar pacientes"),
            ("patients:delete",      "patients",     "Eliminar pacientes"),
            ("appointments:read",    "appointments", "Ver citas"),
            ("appointments:create",  "appointments", "Crear citas"),
            ("appointments:update",  "appointments", "Actualizar citas"),
            ("appointments:cancel",  "appointments", "Cancelar citas"),
            ("doctors:read",         "doctors",      "Ver doctores"),
            ("doctors:availability", "doctors",      "Gestionar disponibilidad"),
            ("inventory:read",       "inventory",    "Ver inventario"),
            ("inventory:create",     "inventory",    "Crear medicamentos / lotes"),
            ("inventory:update",     "inventory",    "Actualizar inventario"),
            ("inventory:adjust",     "inventory",    "Ajustar stock / despachos"),
            ("users:read",           "auth",         "Ver usuarios"),
            ("users:create",         "auth",         "Crear usuarios"),
            ("users:update",         "auth",         "Actualizar usuarios"),
            ("users:deactivate",     "auth",         "Desactivar usuarios"),
            ("roles:read",           "auth",         "Ver roles y permisos"),
            ("roles:assign",         "auth",         "Asignar roles a usuarios"),
            ("reports:view",         "reports",      "Ver reportes"),
            ("reports:export",       "reports",      "Exportar reportes"),
            ("profile:read",         "auth",         "Ver perfil propio"),
            ("profile:update",       "auth",         "Actualizar perfil propio"),
            ("dashboard:view",       "dashboard",    "Ver dashboard / KPIs"),
        ]
        perms = {}
        for code, module, desc in permission_defs:
            row = await fetch_scalar(
                s, "SELECT id FROM permissions WHERE code = :c", {"c": code}
            )
            if row:
                perms[code] = row
            else:
                pid = uid()
                await q(
                    s,
                    "INSERT INTO permissions (id, code, module, description) "
                    "VALUES (:id, :c, :m, :d)",
                    {"id": pid, "c": code, "m": module, "d": desc},
                )
                perms[code] = pid
        await s.commit()
        print(f"  Permissions: {len(perms)}")

        # Role → permissions matrix
        all_codes = [c for c, _, _ in permission_defs]
        role_permission_matrix = {
            "admin": all_codes,
            "doctor": [
                "patients:read",
                "appointments:read",
                "appointments:cancel",
                "doctors:read",
                "doctors:availability",
                "reports:view",
                "profile:read",
                "profile:update",
                "dashboard:view",
            ],
            "analista": [
                "patients:read", "patients:create", "patients:update",
                "appointments:read", "appointments:create",
                "appointments:update", "appointments:cancel",
                "doctors:read", "doctors:availability",
                "reports:view", "reports:export",
                "profile:read", "profile:update",
                "dashboard:view",
            ],
            "farmacia": [
                "inventory:read", "inventory:create",
                "inventory:update", "inventory:adjust",
                "patients:read",
                "profile:read", "profile:update",
                "dashboard:view",
            ],
            "paciente": [
                "appointments:read", "appointments:create", "appointments:cancel",
                "profile:read", "profile:update",
            ],
        }
        rp_count = 0
        for role_name, codes in role_permission_matrix.items():
            role_id = roles[role_name]
            for code in codes:
                perm_id = perms[code]
                exists = await fetch_scalar(
                    s,
                    "SELECT id FROM role_permissions "
                    "WHERE fk_role_id = :r AND fk_permission_id = :p",
                    {"r": role_id, "p": perm_id},
                )
                if exists:
                    continue
                await q(
                    s,
                    "INSERT INTO role_permissions (id, fk_role_id, fk_permission_id) "
                    "VALUES (:id, :r, :p)",
                    {"id": uid(), "r": role_id, "p": perm_id},
                )
                rp_count += 1
        await s.commit()
        print(f"  Role-permissions: {rp_count} new links")

        # ── 2. Users ─────────────────────────────────────────────
        users = {}
        user_defs = [
            ("admin@camiula.edu.ve",       "Administrador CAMIULA",     "admin"),
            ("dr.mendez@camiula.edu.ve",   "Dr. Carlos Mendez",         "doctor"),
            ("dr.lopez@camiula.edu.ve",    "Dra. Ana Lopez",            "doctor"),
            ("dr.garcia@camiula.edu.ve",   "Dr. Roberto Garcia",        "doctor"),
            ("dr.torres@camiula.edu.ve",   "Dr. Miguel Torres",         "doctor"),
            ("dr.romero@camiula.edu.ve",   "Dra. Patricia Romero",      "doctor"),
            ("analista@camiula.edu.ve",    "Maria Analista",            "analista"),
            ("farmacia@camiula.edu.ve",    "Pedro Blanco",              "farmacia"),
            ("farmacia2@camiula.edu.ve",   "Luisa Fernandez",           "farmacia"),
        ]
        for email, name, role in user_defs:
            row = await fetch_scalar(s, "SELECT id FROM users WHERE email = :e", {"e": email})
            if row:
                users[email] = row
            else:
                user_id = uid()
                await q(
                    s,
                    "INSERT INTO users (id, email, full_name, hashed_password, user_status) "
                    "VALUES (:id, :e, :n, :pw, 'ACTIVE')",
                    {"id": user_id, "e": email, "n": name, "pw": hash_password("Test12345")},
                )
                users[email] = user_id
                await q(
                    s,
                    "INSERT INTO user_roles (id, fk_user_id, fk_role_id) VALUES (:id, :uid, :rid)",
                    {"id": uid(), "uid": user_id, "rid": roles[role]},
                )
        await s.commit()
        print(f"  Users: {len(users)}")

        # ── 3. Specialties ────────────────────────────────────────
        specs = {}
        for name in [
            "Medicina General", "Cardiologia", "Pediatria",
            "Psicologia", "Odontologia", "Traumatologia",
            "Ginecologia", "Neurologia",
        ]:
            row = await fetch_scalar(s, "SELECT id FROM specialties WHERE name = :n", {"n": name})
            if row:
                specs[name] = row
            else:
                sid = uid()
                await q(s, "INSERT INTO specialties (id, name) VALUES (:id, :n)", {"id": sid, "n": name})
                specs[name] = sid
        await s.commit()
        print(f"  Specialties: {len(specs)}")

        # ── 3b. Form schemas (linked to real specialty UUIDs) ────
        # Loads scripts/schemas_seed_data.json and inserts each schema
        # using the REAL specialty UUID resolved by normalized name.
        # Avoids the bug in seed_form_schemas.py where the slug literal
        # ("cardiologia") was inserted as specialty_id when name match failed.
        schemas_file = ROOT / "scripts" / "schemas_seed_data.json"
        if schemas_file.exists():
            with open(schemas_file) as f:
                schemas_data = json.load(f)

            # Build {normalized_key: real_uuid} from the specialties just created
            spec_by_key = {normalize_specialty_key(name): sid for name, sid in specs.items()}

            # Clean ALL existing form_schemas to avoid stale rows with bogus
            # specialty_id values from previous runs of seed_form_schemas.py
            await q(s, "DELETE FROM form_schemas")
            await s.commit()

            fs_created = 0
            fs_skipped = 0
            for schema in schemas_data:
                name = schema["specialty_name"]
                key = normalize_specialty_key(name)
                real_id = spec_by_key.get(key)
                if not real_id:
                    print(f"    ⚠ skipped '{name}' — no matching specialty in DB")
                    fs_skipped += 1
                    continue

                await q(
                    s,
                    "INSERT INTO form_schemas "
                    "(id, specialty_id, specialty_name, version, schema_json, status, created_at) "
                    "VALUES (:id, :sid, :sn, :v, CAST(:sj AS jsonb), 'A', NOW())",
                    {
                        "id": uid(),
                        "sid": real_id,
                        "sn": name,
                        "v": schema["version"],
                        "sj": json.dumps(schema["schema_json"]),
                    },
                )
                fs_created += 1
            await s.commit()
            print(f"  Form schemas: {fs_created} created, {fs_skipped} skipped")
        else:
            print("  Form schemas: schemas_seed_data.json not found — skipped")

        # ── 4. Doctors + availability ─────────────────────────────
        doctors = {}
        doctor_defs = [
            ("dr.mendez@camiula.edu.ve",  "Carlos",   "Mendez",  "Medicina General"),
            ("dr.lopez@camiula.edu.ve",   "Ana",      "Lopez",   "Cardiologia"),
            ("dr.garcia@camiula.edu.ve",  "Roberto",  "Garcia",  "Pediatria"),
            ("dr.torres@camiula.edu.ve",  "Miguel",   "Torres",  "Traumatologia"),
            ("dr.romero@camiula.edu.ve",  "Patricia", "Romero",  "Ginecologia"),
        ]
        for email, first, last, spec in doctor_defs:
            row = await fetch_scalar(s, "SELECT id FROM doctors WHERE fk_user_id = :u", {"u": users[email]})
            if row:
                doctors[f"{first} {last}"] = row
            else:
                did = uid()
                await q(
                    s,
                    "INSERT INTO doctors (id, fk_user_id, fk_specialty_id, first_name, last_name, doctor_status) "
                    "VALUES (:id, :uid, :sid, :fn, :ln, 'ACTIVE')",
                    {"id": did, "uid": users[email], "sid": specs[spec], "fn": first, "ln": last},
                )
                doctors[f"{first} {last}"] = did
                for dow in range(1, 6):
                    await q(
                        s,
                        "INSERT INTO doctor_availability (id, fk_doctor_id, day_of_week, start_time, end_time, slot_duration) "
                        "VALUES (:id, :did, :dow, :st, :et, 30)",
                        {"id": uid(), "did": did, "dow": dow, "st": time(8, 0), "et": time(14, 0)},
                    )
        await s.commit()
        print(f"  Doctors: {len(doctors)}")

        # ── 5. Patients (25 realistic Venezuelan patients) ────────
        patients = []
        patient_defs = [
            # (first, last, sex, birth_year, relation, dni_num)
            ("Juan",       "Perez Rojas",       "M", 1985, "estudiante",  12345678),
            ("Maria",      "Garcia Mendez",     "F", 1992, "estudiante",  15678234),
            ("Carlos",     "Rodriguez Silva",   "M", 1978, "docente",     8765432),
            ("Ana",        "Martinez Vargas",   "F", 1990, "personal",    18234567),
            ("Luis",       "Hernandez Paz",     "M", 2002, "estudiante",  27456789),
            ("Sofia",      "Diaz Gonzalez",     "F", 1995, "estudiante",  22345678),
            ("Pedro",      "Sanchez Mora",      "M", 1970, "docente",     5678901),
            ("Laura",      "Ramirez Ortiz",     "F", 1988, "personal",    14567890),
            ("Diego",      "Torres Blanco",     "M", 2001, "estudiante",  26789012),
            ("Valentina",  "Flores Castillo",   "F", 2003, "estudiante",  29012345),
            ("Andres",     "Morales Fuentes",   "M", 1975, "docente",     7890123),
            ("Camila",     "Vargas Suarez",     "F", 1999, "estudiante",  24567890),
            ("Ricardo",    "Castillo Reyes",    "M", 1982, "personal",    10234567),
            ("Isabella",   "Rojas Medina",      "F", 2000, "estudiante",  25678901),
            ("Miguel",     "Navarro Leal",      "M", 1993, "estudiante",  19876543),
            ("Alejandra",  "Vega Bravo",        "F", 1987, "docente",     13456789),
            ("Fernando",   "Salazar Pinto",     "M", 2004, "estudiante",  30123456),
            ("Gabriela",   "Paredes Acosta",    "F", 1996, "familia",     21345678),
            ("Hector",     "Dominguez Rios",    "M", 1968, "externo",     4567890),
            ("Natalia",    "Campos Serrano",    "F", 2002, "estudiante",  27890123),
            ("Oscar",      "Delgado Vera",      "M", 1980, "personal",    11234567),
            ("Paola",      "Ibarra Molina",     "F", 1994, "estudiante",  20345678),
            ("Ramon",      "Espinoza Cruz",     "M", 1972, "docente",     6789012),
            ("Daniela",    "Rios Cabrera",      "F", 1998, "estudiante",  23456789),
            ("Esteban",    "Cordero Pena",      "M", 2005, "estudiante",  31234567),
        ]
        for i, (first, last, sex, birth_year, rel, dni_num) in enumerate(patient_defs):
            nhm = 1000 + i + 1
            dni = f"V-{dni_num}"
            existing = await fetch_scalar(s, "SELECT id FROM patients WHERE nhm = :nhm", {"nhm": nhm})
            if existing:
                patients.append(existing)
                continue
            pid = uid()
            bd = date(birth_year, random.randint(1, 12), random.randint(1, 28))
            await q(
                s,
                "INSERT INTO patients (id, nhm, dni, first_name, last_name, sex, birth_date, "
                "university_relation, is_new, phone, home_address, medical_data, patient_status) "
                "VALUES (:id, :nhm, :dni, :fn, :ln, :sex, :bd, :rel, :new, :ph, :addr, :md, 'active')",
                {
                    "id": pid, "nhm": nhm, "dni": dni, "fn": first, "ln": last,
                    "sex": sex, "bd": bd, "rel": rel, "new": i < 5,
                    "ph": f"0414-{random.randint(1000000, 9999999)}",
                    "addr": f"Av. {random.choice(['Universidad', 'Las Americas', 'Los Proceres', 'Urdaneta'])}, Merida",
                    "md": f'{{"blood_type": "{random.choice(["O+", "A+", "B+", "AB+", "O-"])}", "allergies": []}}',
                },
            )
            patients.append(pid)
        await s.commit()
        print(f"  Patients: {len(patients)}")

        # ── 6. Appointments (50 appointments, well distributed) ───
        doc_ids = list(doctors.values())
        spec_ids = list(specs.values())
        existing_appts = await fetch_scalar(s, "SELECT COUNT(*) FROM appointments")
        if existing_appts == 0:
            statuses = ["atendida"] * 5 + ["confirmada"] * 2 + ["pendiente"] + ["cancelada"]
            for i in range(50):
                ad = today - timedelta(days=random.randint(0, 90))
                h = random.randint(8, 12)
                await q(
                    s,
                    "INSERT INTO appointments (id, fk_patient_id, fk_doctor_id, fk_specialty_id, "
                    "appointment_date, start_time, end_time, duration_minutes, is_first_visit, appointment_status) "
                    "VALUES (:id, :pid, :did, :sid, :ad, :st, :et, 30, :fv, :status)",
                    {
                        "id": uid(), "pid": random.choice(patients),
                        "did": random.choice(doc_ids), "sid": random.choice(spec_ids),
                        "ad": ad, "st": time(h, 0), "et": time(h, 30),
                        "fv": random.random() < 0.3, "status": random.choice(statuses),
                    },
                )
            await s.commit()
            print("  Appointments: 50")
        else:
            print(f"  Appointments: {existing_appts} already exist")

        # ── 7. Categories ─────────────────────────────────────────
        cats = {}
        for name, desc in [
            ("Antibiotico",       "Antibiotics"),
            ("Analgesico",        "Analgesics and pain relievers"),
            ("Antiinflamatorio",  "Anti-inflammatory drugs"),
            ("Antihipertensivo",  "Antihypertensive drugs"),
            ("Antidiabetico",     "Antidiabetic drugs"),
            ("Material medico",   "Medical supplies and consumables"),
            ("Vitaminas",         "Vitamins and supplements"),
        ]:
            row = await fetch_scalar(s, "SELECT id FROM medication_categories WHERE name = :n", {"n": name})
            if row:
                cats[name] = row
            else:
                cid = uid()
                await q(s, "INSERT INTO medication_categories (id, name, description) VALUES (:id, :n, :d)",
                        {"id": cid, "n": name, "d": desc})
                cats[name] = cid
        await s.commit()
        print(f"  Categories: {len(cats)}")

        # ── 8. Medications ────────────────────────────────────────
        meds = {}
        med_defs = [
            ("MED-001", "Amoxicilina",        "tablet",  "500mg",  "Antibiotico"),
            ("MED-002", "Ibuprofeno",          "tablet",  "400mg",  "Analgesico"),
            ("MED-003", "Metformina",          "tablet",  "850mg",  "Antidiabetico"),
            ("MED-004", "Losartan",            "tablet",  "50mg",   "Antihipertensivo"),
            ("MED-005", "Acetaminofen",        "tablet",  "500mg",  "Analgesico"),
            ("MED-006", "Azitromicina",        "tablet",  "500mg",  "Antibiotico"),
            ("MED-007", "Enalapril",           "tablet",  "10mg",   "Antihipertensivo"),
            ("MED-008", "Omeprazol",           "capsule", "20mg",   "Antiinflamatorio"),
            ("MED-009", "Diclofenac",          "tablet",  "50mg",   "Antiinflamatorio"),
            ("MED-010", "Vitamina C",          "tablet",  "500mg",  "Vitaminas"),
            ("MED-011", "Gasas esteriles",     "unit",    None,     "Material medico"),
            ("MED-012", "Guantes latex M",     "unit",    None,     "Material medico"),
        ]
        for code, name, form, conc, cat in med_defs:
            row = await fetch_scalar(s, "SELECT id FROM medications WHERE code = :c", {"c": code})
            if row:
                meds[code] = row
            else:
                mid = uid()
                await q(
                    s,
                    "INSERT INTO medications (id, fk_category_id, code, generic_name, pharmaceutical_form, "
                    "concentration, unit_measure, controlled_substance, requires_refrigeration, medication_status) "
                    "VALUES (:id, :cid, :code, :name, :form, :conc, 'unit', false, false, 'active')",
                    {"id": mid, "cid": cats.get(cat), "code": code, "name": name, "form": form, "conc": conc},
                )
                meds[code] = mid
        await s.commit()
        print(f"  Medications: {len(meds)}")

        # ── 9. Suppliers ──────────────────────────────────────────
        sup_id = await fetch_scalar(s, "SELECT id FROM suppliers LIMIT 1")
        if not sup_id:
            sup_id = uid()
            await q(
                s,
                "INSERT INTO suppliers (id, name, rif, phone, supplier_status) "
                "VALUES (:id, 'Distribuidora Farmaceutica Nacional', 'J-12345678-9', '0212-1234567', 'active')",
                {"id": sup_id},
            )
            sup2 = uid()
            await q(
                s,
                "INSERT INTO suppliers (id, name, rif, phone, supplier_status) "
                "VALUES (:id, 'MedSuply Venezuela C.A.', 'J-98765432-1', '0212-7654321', 'active')",
                {"id": sup2},
            )
            await s.commit()
        print("  Suppliers: ready")

        # ── 10. Batches (3 batches per medication) ────────────────
        med_items = list(meds.items())
        bc = 0
        for code, mid in med_items:
            if not mid:
                continue
            for j in range(3):
                lot = f"LOT-{code}-{j+1:03d}"
                existing = await fetch_scalar(s, "SELECT id FROM batches WHERE lot_number = :lot", {"lot": lot})
                if existing:
                    continue
                qty_rcv = random.choice([200, 300, 500])
                qty_avail = int(qty_rcv * random.uniform(0.4, 0.9))
                exp = today + timedelta(days=random.randint(120, 540))
                rec = today - timedelta(days=random.randint(10, 120))
                await q(
                    s,
                    "INSERT INTO batches (id, fk_medication_id, fk_supplier_id, lot_number, expiration_date, "
                    "quantity_received, quantity_available, received_at, batch_status) "
                    "VALUES (:id, :mid, :sid, :lot, :exp, :qr, :qa, :rec, 'available')",
                    {
                        "id": uid(), "mid": mid, "sid": sup_id, "lot": lot,
                        "exp": exp, "qr": qty_rcv, "qa": qty_avail, "rec": rec,
                    },
                )
                bc += 1
        await s.commit()
        print(f"  Batches: {bc} new")

        print("\nBase seed complete.")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
