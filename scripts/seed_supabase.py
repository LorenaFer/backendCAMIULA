#!/usr/bin/env python3
"""Seed Supabase cloud DB with realistic test data.

Usage:
    DATABASE_URL="postgresql+asyncpg://..." python scripts/seed_supabase.py
"""

import asyncio
import os
import random
import sys
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


async def q(s, sql, p=None):
    """Execute, skip on duplicate."""
    try:
        return await s.execute(text(sql), p or {})
    except Exception as e:
        if "duplicate" in str(e).lower() or "unique" in str(e).lower() or "conflict" in str(e).lower():
            await s.rollback()
            return None
        raise


async def main():
    db_url = os.environ.get("DATABASE_URL", get_settings().DATABASE_URL)
    engine = create_async_engine(db_url)
    S = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with S() as s:
        print("Seeding Supabase...\n")

        # 1. Roles
        roles = {}
        for name in ["admin", "doctor", "analista", "farmacia", "paciente"]:
            r = await s.execute(text("SELECT id FROM roles WHERE name = :n"), {"n": name})
            row = r.scalar()
            if row:
                roles[name] = row
            else:
                rid = uid()
                await q(s, "INSERT INTO roles (id, name) VALUES (:id, :n)", {"id": rid, "n": name})
                roles[name] = rid
        await s.commit()
        print(f"  Roles: {len(roles)}")

        # 2. Users
        users = {}
        for email, name, role in [
            ("admin@camiula.edu.ve", "Administrador CAMIULA", "admin"),
            ("dr.mendez@camiula.edu.ve", "Dr. Carlos Mendez", "doctor"),
            ("dr.lopez@camiula.edu.ve", "Dra. Ana Lopez", "doctor"),
            ("dr.garcia@camiula.edu.ve", "Dr. Roberto Garcia", "doctor"),
            ("analista@camiula.edu.ve", "Maria Analista", "analista"),
            ("farmacia@camiula.edu.ve", "Pedro Farmacia", "farmacia"),
        ]:
            r = await s.execute(text("SELECT id FROM users WHERE email = :e"), {"e": email})
            row = r.scalar()
            if row:
                users[email] = row
            else:
                user_id = uid()
                await q(s, "INSERT INTO users (id, email, full_name, hashed_password, user_status) VALUES (:id, :e, :n, :pw, 'ACTIVE')",
                        {"id": user_id, "e": email, "n": name, "pw": hash_password("Test12345")})
                users[email] = user_id
                await q(s, "INSERT INTO user_roles (id, fk_user_id, fk_role_id) VALUES (:id, :uid, :rid)",
                        {"id": uid(), "uid": user_id, "rid": roles[role]})
        await s.commit()
        print(f"  Users: {len(users)}")

        # 3. Specialties
        specs = {}
        for name in ["Medicina General", "Cardiologia", "Pediatria", "Psicologia", "Odontologia", "Traumatologia"]:
            r = await s.execute(text("SELECT id FROM specialties WHERE name = :n"), {"n": name})
            row = r.scalar()
            if row:
                specs[name] = row
            else:
                sid = uid()
                await q(s, "INSERT INTO specialties (id, name) VALUES (:id, :n)", {"id": sid, "n": name})
                specs[name] = sid
        await s.commit()
        print(f"  Specialties: {len(specs)}")

        # 4. Doctors + availability
        doctors = {}
        for email, first, last, spec in [
            ("dr.mendez@camiula.edu.ve", "Carlos", "Mendez", "Medicina General"),
            ("dr.lopez@camiula.edu.ve", "Ana", "Lopez", "Cardiologia"),
            ("dr.garcia@camiula.edu.ve", "Roberto", "Garcia", "Pediatria"),
        ]:
            r = await s.execute(text("SELECT id FROM doctors WHERE fk_user_id = :u"), {"u": users[email]})
            row = r.scalar()
            if row:
                doctors[f"{first} {last}"] = row
            else:
                did = uid()
                await q(s, "INSERT INTO doctors (id, fk_user_id, fk_specialty_id, first_name, last_name, doctor_status) VALUES (:id, :uid, :sid, :fn, :ln, 'ACTIVE')",
                        {"id": did, "uid": users[email], "sid": specs[spec], "fn": first, "ln": last})
                doctors[f"{first} {last}"] = did
                for dow in range(1, 6):
                    await q(s, "INSERT INTO doctor_availability (id, fk_doctor_id, day_of_week, start_time, end_time, slot_duration) VALUES (:id, :did, :dow, :st, :et, 30)",
                            {"id": uid(), "did": did, "dow": dow, "st": time(8, 0), "et": time(12, 0)})
        await s.commit()
        print(f"  Doctors: {len(doctors)}")

        # 5. Patients
        patients = []
        names = [
            ("Juan", "Perez", "M"), ("Maria", "Garcia", "F"), ("Carlos", "Rodriguez", "M"),
            ("Ana", "Martinez", "F"), ("Luis", "Hernandez", "M"), ("Sofia", "Diaz", "F"),
            ("Pedro", "Sanchez", "M"), ("Laura", "Ramirez", "F"), ("Diego", "Torres", "M"),
            ("Valentina", "Flores", "F"), ("Andres", "Morales", "M"), ("Camila", "Vargas", "F"),
            ("Ricardo", "Castillo", "M"), ("Isabella", "Rojas", "F"), ("Miguel", "Navarro", "M"),
        ]
        rels = ["estudiante", "personal", "docente", "familia", "externo"]
        for i, (first, last, sex) in enumerate(names):
            pid = uid()
            nhm = 1000 + i + 1
            dni = f"V-{random.randint(10000000, 30000000)}"
            bd = date(random.randint(1970, 2005), random.randint(1, 12), random.randint(1, 28))
            await q(s, "INSERT INTO patients (id, nhm, dni, first_name, last_name, sex, birth_date, university_relation, is_new, phone, home_address, medical_data, patient_status) VALUES (:id, :nhm, :dni, :fn, :ln, :sex, :bd, :rel, :new, :ph, :addr, :md, 'active')",
                    {"id": pid, "nhm": nhm, "dni": dni, "fn": first, "ln": last, "sex": sex, "bd": bd, "rel": random.choice(rels), "new": i < 5, "ph": f"0414-{random.randint(1000000, 9999999)}", "addr": f"Av. {random.choice(['Universidad', 'Las Americas'])}, Merida", "md": '{"blood_type": "' + random.choice(["O+", "A+", "B+"]) + '"}'})
            patients.append(pid)
        await s.commit()
        print(f"  Patients: {len(patients)}")

        # 6. Appointments
        doc_ids = list(doctors.values())
        spec_ids = list(specs.values())
        today = date.today()
        for i in range(30):
            ad = today - timedelta(days=random.randint(0, 60))
            h = random.randint(8, 11)
            await q(s, "INSERT INTO appointments (id, fk_patient_id, fk_doctor_id, fk_specialty_id, appointment_date, start_time, end_time, duration_minutes, is_first_visit, appointment_status) VALUES (:id, :pid, :did, :sid, :ad, :st, :et, 30, :fv, :status)",
                    {"id": uid(), "pid": random.choice(patients), "did": random.choice(doc_ids), "sid": random.choice(spec_ids), "ad": ad, "st": time(h, 0), "et": time(h, 30), "fv": random.random() < 0.3, "status": random.choice(["pendiente", "confirmada", "atendida", "cancelada"])})
        await s.commit()
        print(f"  Appointments: 30")

        # 7. Categories
        cats = {}
        for name, desc in [("Antibiotico", "Antibiotics"), ("Analgesico", "Analgesics"), ("Antiinflamatorio", "Anti-inflammatory"), ("Material medico", "Medical supplies")]:
            r = await s.execute(text("SELECT id FROM medication_categories WHERE name = :n"), {"n": name})
            row = r.scalar()
            if row:
                cats[name] = row
            else:
                cid = uid()
                await q(s, "INSERT INTO medication_categories (id, name, description) VALUES (:id, :n, :d)", {"id": cid, "n": name, "d": desc})
                cats[name] = cid
        await s.commit()
        print(f"  Categories: {len(cats)}")

        # 8. Medications
        meds = {}
        for code, name, form, conc, cat in [
            ("MED-001", "Amoxicilina", "tablet", "500mg", "Antibiotico"),
            ("MED-002", "Ibuprofeno", "tablet", "400mg", "Analgesico"),
            ("MED-003", "Metformina", "tablet", "850mg", "Analgesico"),
            ("MED-004", "Losartan", "tablet", "50mg", "Antiinflamatorio"),
            ("MED-005", "Acetaminofen", "tablet", "500mg", "Analgesico"),
            ("MED-006", "Gasas esteriles", "unit", None, "Material medico"),
        ]:
            r = await s.execute(text("SELECT id FROM medications WHERE code = :c"), {"c": code})
            row = r.scalar()
            if row:
                meds[code] = row
            else:
                mid = uid()
                await q(s, "INSERT INTO medications (id, fk_category_id, code, generic_name, pharmaceutical_form, concentration, unit_measure, controlled_substance, requires_refrigeration, medication_status) VALUES (:id, :cid, :code, :name, :form, :conc, 'unit', false, false, 'active')",
                        {"id": mid, "cid": cats.get(cat), "code": code, "name": name, "form": form, "conc": conc})
                meds[code] = mid
        await s.commit()
        print(f"  Medications: {len(meds)}")

        # 9. Supplier
        r = await s.execute(text("SELECT id FROM suppliers LIMIT 1"))
        sup_id = r.scalar()
        if not sup_id:
            sup_id = uid()
            await q(s, "INSERT INTO suppliers (id, name, rif, phone, supplier_status) VALUES (:id, 'Distribuidora Farmaceutica Nacional', 'J-12345678-9', '0212-1234567', 'active')", {"id": sup_id})
            await s.commit()
        print(f"  Suppliers: 1")

        # 10. Batches
        bc = 0
        for code, mid in meds.items():
            if not mid:
                continue
            for j in range(2):
                await q(s, "INSERT INTO batches (id, fk_medication_id, fk_supplier_id, lot_number, expiration_date, quantity_received, quantity_available, received_at, batch_status) VALUES (:id, :mid, :sid, :lot, :exp, :qr, :qa, :rec, 'available')",
                        {"id": uid(), "mid": mid, "sid": sup_id, "lot": f"LOT-{code}-{j+1:03d}", "exp": today + timedelta(days=random.randint(90, 365)), "qr": random.choice([100, 200, 500]), "qa": random.choice([50, 100, 200]), "rec": today - timedelta(days=random.randint(10, 90))})
                bc += 1
        await s.commit()
        print(f"  Batches: {bc}")

        print(f"\nDone! Supabase seeded.")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
