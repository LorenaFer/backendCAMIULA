#!/usr/bin/env python3
"""Seed form schemas from JSON file.

Run: python scripts/seed_form_schemas.py
"""

import asyncio
import json
import sys
import unicodedata
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sqlalchemy import text
from app.shared.database.session import async_session_factory


def normalize_key(name: str) -> str:
    nfkd = unicodedata.normalize("NFKD", name.lower())
    ascii_text = nfkd.encode("ascii", "ignore").decode("ascii")
    return ascii_text.replace(" ", "-").replace("(", "").replace(")", "")


async def seed():
    data_file = ROOT / "scripts" / "schemas_seed_data.json"
    with open(data_file) as f:
        schemas = json.load(f)

    async with async_session_factory() as session:
        # Get specialty IDs from DB
        result = await session.execute(text("SELECT id, name FROM specialties WHERE status = 'A'"))
        db_specialties = {normalize_key(row[1]): row[0] for row in result.fetchall()}

        # Clean old test schemas
        await session.execute(text(
            "DELETE FROM form_schemas WHERE specialty_name LIKE 'Cardiology %' "
            "OR specialty_name LIKE 'Specialty-%'"
        ))

        created = 0
        updated = 0

        for schema in schemas:
            key = schema["specialty_id"]
            name = schema["specialty_name"]
            version = schema["version"]
            schema_json = json.dumps(schema["schema_json"])

            # Resolve real specialty_id from DB
            real_id = db_specialties.get(normalize_key(name), key)

            # Check if exists
            existing = await session.execute(
                text("SELECT id FROM form_schemas WHERE specialty_id = :sid AND status = 'A'"),
                {"sid": real_id},
            )
            row = existing.fetchone()

            if row:
                await session.execute(
                    text(
                        "UPDATE form_schemas SET schema_json = CAST(:sj AS jsonb), "
                        "version = :v, specialty_name = :sn, updated_at = NOW() "
                        "WHERE id = :id"
                    ),
                    {"sj": schema_json, "v": version, "sn": name, "id": row[0]},
                )
                updated += 1
                print(f"  UPDATE {name} (id={real_id[:8]}...)")
            else:
                await session.execute(
                    text(
                        "INSERT INTO form_schemas (id, specialty_id, specialty_name, version, "
                        "schema_json, status, created_at) "
                        "VALUES (:id, :sid, :sn, :v, CAST(:sj AS jsonb), 'A', NOW())"
                    ),
                    {
                        "id": str(uuid4()),
                        "sid": real_id,
                        "sn": name,
                        "v": version,
                        "sj": schema_json,
                    },
                )
                created += 1
                print(f"  CREATE {name} (id={real_id[:8]}...)")

        await session.commit()
        print(f"\nDone: {created} created, {updated} updated")


if __name__ == "__main__":
    asyncio.run(seed())
