#!/usr/bin/env python3
"""Seed mínimo para la base de datos de CI.

Crea exactamente los roles, permisos y usuarios que necesitan los integration
tests, nada más. Es idempotente — seguro de correr varias veces.

Usuarios creados:
  admin@camiula.com     / admin123    → rol admin     (todos los permisos)
  analista@camiula.com  / analista123 → rol analista
  doctor@camiula.com    / doctor123   → rol doctor
  paciente@camiula.com  / paciente123 → rol paciente

Uso (CI):
  DATABASE_URL=... python scripts/seed_ci.py
"""

import asyncio
import os
import sys
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.security import hash_password

uid = lambda: str(uuid4())

# ── Roles ─────────────────────────────────────────────────────
ROLES = ["admin", "analista", "doctor", "farmacia", "paciente"]

# ── Permissions (espejo exacto de seed_local.py) ──────────────
PERMISSION_DEFS = [
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

ALL_CODES = [c for c, _, _ in PERMISSION_DEFS]

# ── Role → Permission matrix (espejo exacto de seed_local.py) ─
ROLE_PERMISSION_MATRIX = {
    "admin": ALL_CODES,
    "doctor": [
        "patients:read",
        "appointments:read", "appointments:cancel",
        "doctors:read", "doctors:availability",
        "reports:view",
        "profile:read", "profile:update",
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

# ── Test users requeridos por los integration tests ────────────
CI_USERS = [
    ("admin@camiula.com",    "Administrador CI",  "admin",    "admin123"),
    ("analista@camiula.com", "Analista CI",        "analista", "analista123"),
    ("doctor@camiula.com",   "Doctor CI",          "doctor",   "doctor123"),
    ("paciente@camiula.com", "Paciente CI",        "paciente", "paciente123"),
]


async def run(db_url: str) -> None:
    engine = create_async_engine(db_url, echo=False)
    Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with Session() as s:

        # ── 1. Roles ──────────────────────────────────────────
        print("[1/4] Roles...")
        role_ids: dict[str, str] = {}
        for name in ROLES:
            row = await s.execute(
                text("SELECT id FROM roles WHERE name = :n"), {"n": name}
            )
            existing = row.scalar()
            if existing:
                role_ids[name] = existing
            else:
                rid = uid()
                await s.execute(
                    text("INSERT INTO roles (id, name) VALUES (:id, :n)"),
                    {"id": rid, "n": name},
                )
                role_ids[name] = rid
                print(f"  + role '{name}'")
        await s.commit()

        # ── 2. Permissions ────────────────────────────────────
        print("[2/4] Permissions...")
        perm_ids: dict[str, str] = {}
        for code, module, desc in PERMISSION_DEFS:
            row = await s.execute(
                text("SELECT id FROM permissions WHERE code = :c"), {"c": code}
            )
            existing = row.scalar()
            if existing:
                perm_ids[code] = existing
            else:
                pid = uid()
                await s.execute(
                    text(
                        "INSERT INTO permissions (id, code, module, description) "
                        "VALUES (:id, :c, :m, :d)"
                    ),
                    {"id": pid, "c": code, "m": module, "d": desc},
                )
                perm_ids[code] = pid
                print(f"  + permission '{code}'")
        await s.commit()

        # ── 3. Role → Permission links ────────────────────────
        print("[3/4] Role-permission links...")
        rp_count = 0
        for role_name, codes in ROLE_PERMISSION_MATRIX.items():
            role_id = role_ids[role_name]
            for code in codes:
                perm_id = perm_ids[code]
                exists = await s.execute(
                    text(
                        "SELECT id FROM role_permissions "
                        "WHERE fk_role_id = :r AND fk_permission_id = :p"
                    ),
                    {"r": role_id, "p": perm_id},
                )
                if not exists.scalar():
                    await s.execute(
                        text(
                            "INSERT INTO role_permissions (id, fk_role_id, fk_permission_id) "
                            "VALUES (:id, :r, :p)"
                        ),
                        {"id": uid(), "r": role_id, "p": perm_id},
                    )
                    rp_count += 1
        await s.commit()
        print(f"  -> {rp_count} links created")

        # ── 4. Users + role assignment ────────────────────────
        print("[4/4] Users...")
        for email, full_name, role, password in CI_USERS:
            row = await s.execute(
                text("SELECT id FROM users WHERE email = :e"), {"e": email}
            )
            existing_id = row.scalar()

            if existing_id:
                user_id = existing_id
            else:
                user_id = uid()
                await s.execute(
                    text(
                        "INSERT INTO users (id, email, full_name, hashed_password, user_status) "
                        "VALUES (:id, :e, :n, :pw, 'ACTIVE')"
                    ),
                    {
                        "id": user_id,
                        "e": email,
                        "n": full_name,
                        "pw": hash_password(password),
                    },
                )
                print(f"  + user '{email}' [{role}]")

            # Ensure role assigned (idempotent)
            role_id = role_ids[role]
            link = await s.execute(
                text(
                    "SELECT id FROM user_roles "
                    "WHERE fk_user_id = :u AND fk_role_id = :r"
                ),
                {"u": user_id, "r": role_id},
            )
            if not link.scalar():
                await s.execute(
                    text(
                        "INSERT INTO user_roles (id, fk_user_id, fk_role_id) "
                        "VALUES (:id, :u, :r)"
                    ),
                    {"id": uid(), "u": user_id, "r": role_id},
                )
                print(f"    → role '{role}' assigned")

        await s.commit()

    await engine.dispose()
    print("\n✅ CI seed complete")


if __name__ == "__main__":
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("ERROR: DATABASE_URL not set", file=sys.stderr)
        sys.exit(1)
    asyncio.run(run(db_url))
