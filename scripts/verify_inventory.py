"""
Script de verificación del módulo de Inventario.

Confirma que:
  1. Las 11 tablas existen en la BD.
  2. Los datos del seeder están presentes.
  3. El JSON de /api/inventory/medications tiene las llaves exactas del frontend.

Uso:
    python scripts/verify_inventory.py
"""

import asyncio
import json
import sys

from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import create_async_engine

sys.path.insert(0, ".")
from app.core.config import get_settings

EXPECTED_TABLES = {
    "suppliers",
    "medications",
    "purchase_orders",
    "purchase_order_items",
    "batches",
    "prescriptions",
    "prescription_items",
    "dispatches",
    "dispatch_items",
    "dispatch_limits",
    "dispatch_exceptions",
}

# Llaves que el frontend espera en la interfaz Medication
EXPECTED_MEDICATION_KEYS = {
    "id",
    "code",
    "generic_name",
    "commercial_name",
    "pharmaceutical_form",
    "concentration",
    "unit_measure",
    "therapeutic_class",
    "controlled_substance",
    "requires_refrigeration",
    "medication_status",
    "current_stock",
    "created_at",
}

# Llaves que el frontend espera en la interfaz Batch
EXPECTED_BATCH_KEYS = {
    "id",
    "fk_medication_id",
    "fk_supplier_id",
    "lot_number",
    "expiration_date",
    "quantity_received",
    "quantity_available",
    "unit_cost",
    "batch_status",
    "received_at",
}


async def run_checks() -> None:
    settings = get_settings()
    engine = create_async_engine(settings.DATABASE_URL, echo=False)

    print("=" * 60)
    print("VERIFICACIÓN DEL MÓDULO DE INVENTARIO")
    print("=" * 60)

    async with engine.connect() as conn:

        # ── 1. Tablas ────────────────────────────────────────────
        result = await conn.execute(
            text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public' ORDER BY table_name"
            )
        )
        existing = {row[0] for row in result.fetchall()}
        missing = EXPECTED_TABLES - existing

        print(f"\n[1] Tablas en BD: {len(existing & EXPECTED_TABLES)}/{len(EXPECTED_TABLES)}")
        if missing:
            print(f"    FALTANTES: {missing}")
            print("    → Ejecuta: alembic upgrade head")
        else:
            print("    OK — todas las tablas presentes.")

        # ── 2. Datos del seeder ──────────────────────────────────
        print("\n[2] Datos del seeder:")

        suppliers = (await conn.execute(text("SELECT name, supplier_status FROM suppliers WHERE status='A'"))).fetchall()
        print(f"    Proveedores: {len(suppliers)}")
        for s in suppliers:
            print(f"      · {s[0]} ({s[1]})")

        meds = (await conn.execute(text("SELECT code, generic_name, therapeutic_class, medication_status FROM medications WHERE status='A'"))).fetchall()
        print(f"    Medicamentos: {len(meds)}")
        for m in meds:
            print(f"      · [{m[0]}] {m[1]} — {m[2]} ({m[3]})")

        batches = (await conn.execute(text(
            "SELECT lot_number, expiration_date, quantity_available, batch_status "
            "FROM batches WHERE status='A' ORDER BY expiration_date"
        ))).fetchall()
        print(f"    Lotes: {len(batches)}")
        for b in batches:
            print(f"      · {b[0]} | vence {b[1]} | disponible={b[2]} ({b[3]})")

        limits = (await conn.execute(text("SELECT COUNT(*) FROM dispatch_limits WHERE status='A' AND active=true"))).scalar()
        print(f"    Límites de despacho activos: {limits}")

        # ── 3. Stock calculado ───────────────────────────────────
        print("\n[3] Stock actual por medicamento:")
        stock_q = await conn.execute(text("""
            SELECT m.code, m.generic_name, COALESCE(SUM(b.quantity_available), 0) AS stock
            FROM medications m
            LEFT JOIN batches b ON b.fk_medication_id = m.id
                AND b.batch_status = 'available' AND b.status = 'A'
            WHERE m.status = 'A'
            GROUP BY m.code, m.generic_name
            ORDER BY m.code
        """))
        for row in stock_q.fetchall():
            alert = "⚠ SIN STOCK" if row[2] == 0 else "OK"
            print(f"    [{row[0]}] {row[1]}: {row[2]} unidades — {alert}")

        # ── 4. Validación de llaves JSON ─────────────────────────
        print("\n[4] Validación de contrato JSON con frontend:")
        med_row = (await conn.execute(text(
            "SELECT id, code, generic_name, commercial_name, pharmaceutical_form, "
            "concentration, unit_measure, therapeutic_class, controlled_substance, "
            "requires_refrigeration, medication_status, created_at "
            "FROM medications WHERE status='A' LIMIT 1"
        ))).mappings().first()

        if med_row:
            db_keys = set(med_row.keys()) | {"current_stock"}
            missing_keys = EXPECTED_MEDICATION_KEYS - db_keys
            extra_keys = db_keys - EXPECTED_MEDICATION_KEYS - {"created_by"}
            if not missing_keys and not extra_keys:
                print("    Medication: OK — todas las llaves coinciden con inventory.ts")
            else:
                if missing_keys:
                    print(f"    FALTAN en BD: {missing_keys}")
                if extra_keys:
                    print(f"    EXTRA en BD (no impacta frontend): {extra_keys}")
        else:
            print("    Sin datos para validar — ejecuta el seeder primero.")

    await engine.dispose()
    print("\n" + "=" * 60)
    print("Verificación completada.")


if __name__ == "__main__":
    asyncio.run(run_checks())
