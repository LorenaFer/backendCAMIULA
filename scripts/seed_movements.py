"""Seeder: genera movimientos de inventario y alertas de stock realistas.

Uso:
    python scripts/seed_movements.py

Genera ~60 movimientos (entradas y salidas) distribuidos en los últimos 90 días
para los medicamentos reales de la BD. También genera alertas de stock.
"""

import asyncio
import random
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings


async def main():
    settings = get_settings()
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # ── 1. Get real medications ──────────────────────────────
        result = await session.execute(text(
            "SELECT id, code, generic_name FROM medications "
            "WHERE status = 'A' AND medication_status = 'active' "
            "ORDER BY code LIMIT 20"
        ))
        medications = result.all()

        if not medications:
            print("No medications found. Seed medications first.")
            return

        # ── 2. Get real batches ──────────────────────────────────
        result = await session.execute(text(
            "SELECT id, fk_medication_id, lot_number, fk_purchase_order_id "
            "FROM batches WHERE status = 'A' LIMIT 30"
        ))
        batches = result.all()
        batches_by_med = {}
        for b in batches:
            batches_by_med.setdefault(b[1], []).append(b)

        # ── 3. Get real purchase orders ──────────────────────────
        result = await session.execute(text(
            "SELECT id, order_number FROM purchase_orders "
            "WHERE status = 'A' LIMIT 10"
        ))
        purchase_orders = result.all()

        # ── 4. Clear existing seed data ──────────────────────────
        await session.execute(text("DELETE FROM inventory_movements"))
        await session.execute(text("DELETE FROM stock_alerts"))
        print("Cleared existing movements and alerts.")

        # ── 5. Generate movements ────────────────────────────────
        now = datetime.now(timezone.utc)
        movements = []

        for med in medications:
            med_id = med[0]
            med_code = med[1]
            med_name = med[2]
            med_batches = batches_by_med.get(med_id, [])

            # Running balance simulation
            balance = 0

            # Generate 3-8 movements per medication over the last 90 days
            num_movements = random.randint(3, 8)
            base_date = now - timedelta(days=90)

            # Sort movement dates chronologically
            days_offsets = sorted(random.sample(range(0, 90), min(num_movements, 90)))

            for i, day_offset in enumerate(days_offsets):
                movement_date = base_date + timedelta(
                    days=day_offset,
                    hours=random.randint(7, 17),
                    minutes=random.randint(0, 59),
                )

                # First 1-2 movements are always entries, then mix
                if i < 2 or random.random() < 0.4:
                    # ENTRY
                    qty = random.choice([20, 30, 50, 100, 150, 200, 250, 500])
                    balance += qty

                    batch = random.choice(med_batches) if med_batches else None
                    po = random.choice(purchase_orders) if purchase_orders else None

                    lot_numbers = [
                        f"LOT-{movement_date.strftime('%Y%m')}-{random.randint(1,99):03d}",
                        f"LOT-{med_code}-{random.randint(100,999)}",
                    ]

                    movements.append({
                        "id": str(uuid4()),
                        "fk_medication_id": med_id,
                        "fk_batch_id": batch[0] if batch else None,
                        "fk_dispatch_id": None,
                        "fk_purchase_order_id": po[0] if po else None,
                        "movement_type": "entry",
                        "quantity": qty,
                        "balance_after": balance,
                        "reference": f"OC {po[1]}" if po else f"Ingreso manual {med_code}",
                        "lot_number": random.choice(lot_numbers),
                        "unit_cost": round(random.uniform(0.50, 25.00), 2),
                        "notes": random.choice([
                            None,
                            "Recepcion de orden de compra",
                            "Ingreso por donacion",
                            "Reposicion de stock",
                            f"Lote recibido — {med_name}",
                        ]),
                        "movement_date": movement_date,
                        "created_by": "system-seeder",
                    })
                else:
                    # EXIT
                    max_exit = min(balance, random.choice([5, 10, 15, 20, 30, 50]))
                    if max_exit <= 0:
                        continue
                    qty = random.randint(1, max_exit)
                    balance -= qty

                    batch = random.choice(med_batches) if med_batches else None

                    movements.append({
                        "id": str(uuid4()),
                        "fk_medication_id": med_id,
                        "fk_batch_id": batch[0] if batch else None,
                        "fk_dispatch_id": None,
                        "fk_purchase_order_id": None,
                        "movement_type": "exit",
                        "quantity": -qty,
                        "balance_after": balance,
                        "reference": f"Despacho RX-{random.randint(1000,9999)}",
                        "lot_number": batch[2] if batch else None,
                        "unit_cost": None,
                        "notes": random.choice([
                            None,
                            "Despacho a paciente",
                            "Despacho farmacia",
                            "Consulta ambulatoria",
                        ]),
                        "movement_date": movement_date,
                        "created_by": "system-seeder",
                    })

            # Add an occasional adjustment
            if random.random() < 0.3 and balance > 0:
                adj_qty = random.choice([-2, -1, 1, 2, -5, 3])
                balance += adj_qty
                if balance < 0:
                    balance = 0
                movements.append({
                    "id": str(uuid4()),
                    "fk_medication_id": med_id,
                    "fk_batch_id": None,
                    "fk_dispatch_id": None,
                    "fk_purchase_order_id": None,
                    "movement_type": "adjustment",
                    "quantity": adj_qty,
                    "balance_after": balance,
                    "reference": f"Ajuste inventario fisico",
                    "lot_number": None,
                    "unit_cost": None,
                    "notes": random.choice([
                        "Ajuste por conteo fisico",
                        "Correccion de inventario",
                        "Diferencia detectada en auditoria",
                    ]),
                    "movement_date": now - timedelta(days=random.randint(1, 10)),
                    "created_by": "system-seeder",
                })

        # ── 6. Insert movements ──────────────────────────────────
        for m in movements:
            await session.execute(text("""
                INSERT INTO inventory_movements (
                    id, fk_medication_id, fk_batch_id, fk_dispatch_id,
                    fk_purchase_order_id, movement_type, quantity,
                    balance_after, reference, lot_number, unit_cost,
                    notes, movement_date, created_by
                ) VALUES (
                    :id, :fk_medication_id, :fk_batch_id, :fk_dispatch_id,
                    :fk_purchase_order_id, :movement_type, :quantity,
                    :balance_after, :reference, :lot_number, :unit_cost,
                    :notes, :movement_date, :created_by
                )
            """), m)

        print(f"Inserted {len(movements)} inventory movements.")

        # ── 7. Generate stock alerts ─────────────────────────────
        alerts = []
        for med in medications:
            med_id = med[0]
            med_name = med[2]

            # Get current stock
            result = await session.execute(text(
                "SELECT COALESCE(SUM(quantity_available), 0) "
                "FROM batches WHERE fk_medication_id = :mid "
                "AND status = 'A' AND batch_status = 'available'"
            ), {"mid": med_id})
            stock = int(result.scalar())

            # Determine alert level
            if stock == 0:
                level, threshold = "expired", 0
                msg = f"{med_name}: stock agotado (0 unidades)"
            elif stock <= 10:
                level, threshold = "critical", 10
                msg = f"{med_name}: stock critico ({stock} <= 10 unidades)"
            elif stock <= 50:
                level, threshold = "low", 50
                msg = f"{med_name}: stock bajo ({stock} <= 50 unidades)"
            else:
                continue  # Stock OK, no alert

            detected = now - timedelta(days=random.randint(1, 30))

            # Some alerts are resolved, some active
            is_resolved = random.random() < 0.3
            alert_status = "resolved" if is_resolved else "active"
            resolved_at = (detected + timedelta(days=random.randint(1, 5))) if is_resolved else None

            alerts.append({
                "id": str(uuid4()),
                "fk_medication_id": med_id,
                "alert_level": level,
                "current_stock": stock,
                "threshold": threshold,
                "message": msg,
                "detected_at": detected,
                "resolved_at": resolved_at,
                "resolved_by": "system-seeder" if is_resolved else None,
                "alert_status": alert_status,
                "created_by": "system-seeder",
            })

        for a in alerts:
            await session.execute(text("""
                INSERT INTO stock_alerts (
                    id, fk_medication_id, alert_level, current_stock,
                    threshold, message, detected_at, resolved_at,
                    resolved_by, alert_status, created_by
                ) VALUES (
                    :id, :fk_medication_id, :alert_level, :current_stock,
                    :threshold, :message, :detected_at, :resolved_at,
                    :resolved_by, :alert_status, :created_by
                )
            """), a)

        print(f"Inserted {len(alerts)} stock alerts.")

        await session.commit()
        print("\nDone! Summary:")
        print(f"  Medications with movements: {len(medications)}")
        print(f"  Total movements: {len(movements)}")
        print(f"  Total alerts: {len(alerts)}")
        print(f"  Active alerts: {sum(1 for a in alerts if a['alert_status'] == 'active')}")
        print(f"  Resolved alerts: {sum(1 for a in alerts if a['alert_status'] == 'resolved')}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
