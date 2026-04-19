#!/usr/bin/env python3
"""Seed mínimo para la base de datos de CI.

Crea exactamente los roles y usuarios que necesitan los integration tests,
nada más. Es idempotente — seguro de correr varias veces.

Usuarios creados:
  admin@camiula.com     / admin123    → rol admin
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

ROLES = ["admin", "analista", "doctor", "farmacia", "paciente"]

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
        # ── Roles ─────────────────────────────────────────────
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
                print(f"  + role '{name}' created")

        await s.commit()

        # ── Users + role assignment ────────────────────────────
        for email, full_name, role, password in CI_USERS:
            row = await s.execute(
                text("SELECT id FROM users WHERE email = :e"), {"e": email}
            )
            existing_id = row.scalar()

            if existing_id:
                print(f"  = user '{email}' already exists")
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
                print(f"  + user '{email}' [{role}] created")

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
