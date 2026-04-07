#!/usr/bin/env python3
"""Seed Supabase with operational data: prescriptions, dispatches, movements,
medical records, medical orders, dispatch limits, and stock alerts.

Assumes seed_supabase.py has already run (roles, users, doctors, patients, meds, batches).

Usage:
    DATABASE_URL="postgresql+asyncpg://..." python scripts/seed_supabase_extra.py
"""

import asyncio
import os
import random
import sys
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings

uid = lambda: str(uuid4())
today = date.today()
now = datetime.now(timezone.utc)


async def fetch_all(s, sql, p=None):
    r = await s.execute(text(sql), p or {})
    return r.fetchall()


async def fetch_one(s, sql, p=None):
    r = await s.execute(text(sql), p or {})
    return r.fetchone()


async def safe_insert(s, sql, p=None):
    try:
        return await s.execute(text(sql), p or {})
    except Exception as e:
        msg = str(e).lower()
        if any(k in msg for k in ("duplicate", "unique", "conflict")):
            await s.rollback()
            return None
        raise


async def main():
    db_url = os.environ.get("DATABASE_URL", get_settings().DATABASE_URL)
    masked = db_url.split("@")[-1] if "@" in db_url else db_url
    print(f"Target DB: ...@{masked}\n")

    engine = create_async_engine(db_url)
    Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with Session() as s:
        # ── Load base data ────────────────────────────────────────
        patients = [r[0] for r in await fetch_all(s, "SELECT id FROM patients ORDER BY nhm")]
        doctors = await fetch_all(s, "SELECT id, first_name, last_name FROM doctors")
        doctor_ids = [r[0] for r in doctors]
        meds = await fetch_all(s, "SELECT id, code, generic_name FROM medications ORDER BY code")
        med_tuples = [(r[0], r[1], r[2]) for r in meds]
        batches = await fetch_all(
            s,
            "SELECT id, fk_medication_id, lot_number, quantity_available FROM batches "
            "WHERE batch_status = 'available' AND quantity_available > 0",
        )
        r = await fetch_one(s, "SELECT id FROM users WHERE email = 'farmacia@camiula.edu.ve'")
        pharmacist1 = r[0] if r else None
        r2 = await fetch_one(s, "SELECT id FROM users WHERE email = 'farmacia2@camiula.edu.ve'")
        pharmacist2 = r2[0] if r2 else pharmacist1
        pharmacists = [x for x in [pharmacist1, pharmacist2] if x]
        sup = await fetch_one(s, "SELECT id FROM suppliers LIMIT 1")
        sup_id = sup[0] if sup else None

        if not patients or not doctor_ids or not meds or not batches:
            print("ERROR: run seed_supabase.py first.")
            return

        print(f"  Loaded: {len(patients)} patients, {len(doctor_ids)} doctors, "
              f"{len(meds)} meds, {len(batches)} batches")

        # ── 1. Purchase Orders ────────────────────────────────────
        existing_pos = (await fetch_one(s, "SELECT COUNT(*) FROM purchase_orders"))[0]
        if existing_pos == 0 and sup_id:
            po_statuses = ["received", "received", "received", "sent", "partial"]
            for i in range(5):
                po_id = uid()
                order_num = f"PO-2026-{i+1:04d}"
                order_date = today - timedelta(days=random.randint(10, 75))
                st = po_statuses[i % len(po_statuses)]
                await s.execute(text(
                    "INSERT INTO purchase_orders (id, fk_supplier_id, order_number, order_date, "
                    "expected_date, order_status, notes) VALUES (:id, :sup, :num, :od, :ed, :st, :n)"
                ), {
                    "id": po_id, "sup": sup_id, "num": order_num,
                    "od": order_date, "ed": order_date + timedelta(days=14),
                    "st": st, "n": f"Pedido mensual #{i+1}",
                })
                sample_meds = random.sample(med_tuples, min(4, len(med_tuples)))
                for med_id, code, _ in sample_meds:
                    qty = random.choice([100, 200, 300, 500])
                    received = qty if st == "received" else (qty // 2 if st == "partial" else 0)
                    await s.execute(text(
                        "INSERT INTO purchase_order_items (id, fk_purchase_order_id, fk_medication_id, "
                        "quantity_ordered, quantity_received, unit_cost, item_status) "
                        "VALUES (:id, :poid, :mid, :qo, :qr, :cost, :st)"
                    ), {
                        "id": uid(), "poid": po_id, "mid": med_id,
                        "qo": qty, "qr": received,
                        "cost": round(random.uniform(0.5, 20.0), 2),
                        "st": "received" if received == qty else ("partial" if received > 0 else "pending"),
                    })
            await s.commit()
            print(f"  + Purchase Orders: 5 (with items)")
        else:
            print(f"  = Purchase Orders: {existing_pos} already exist")

        # ── 2. Attended appointments for prescriptions ────────────
        attended = await fetch_all(
            s,
            "SELECT id, fk_patient_id, fk_doctor_id FROM appointments "
            "WHERE appointment_status IN ('atendida', 'confirmada') ORDER BY appointment_date DESC LIMIT 25",
        )
        if not attended:
            print("  WARNING: No attended appointments. Prescriptions may be sparse.")

        # ── 3. Prescriptions ──────────────────────────────────────
        existing_rx = (await fetch_one(s, "SELECT COUNT(*) FROM prescriptions"))[0]
        if existing_rx == 0:
            rx_count = 0
            # Common dosage instructions
            doses = [
                "1 tableta cada 8 horas por 7 dias",
                "1 tableta cada 12 horas por 10 dias",
                "2 tabletas al dia por 5 dias",
                "1 tableta al dia en ayunas",
                "1 tableta cada 6 horas segun dolor",
            ]
            rx_notes = [
                "Tomar con alimentos para evitar malestar gastrico",
                "No combinar con alcohol durante el tratamiento",
                "Tomar con abundante agua",
                "Suspender si presenta reacciones alergicas",
                None, None,
            ]
            rx_statuses = ["dispensed"] * 8 + ["issued"] * 4 + ["draft"] * 2

            for appt_id, patient_id, doctor_id in attended[:20]:
                rx_id = uid()
                rx_num = f"RX-2026-{rx_count+1:05d}"
                rx_date = today - timedelta(days=random.randint(1, 60))
                rx_status = random.choice(rx_statuses)
                await s.execute(text(
                    "INSERT INTO prescriptions (id, fk_appointment_id, fk_patient_id, fk_doctor_id, "
                    "prescription_number, prescription_date, notes, prescription_status) "
                    "VALUES (:id, :aid, :pid, :did, :num, :rd, :n, :st)"
                ), {
                    "id": rx_id, "aid": appt_id, "pid": patient_id, "did": doctor_id,
                    "num": rx_num, "rd": rx_date, "n": random.choice(rx_notes), "st": rx_status,
                })
                # 1-3 items per prescription
                n_items = random.randint(1, min(3, len(med_tuples)))
                for med_id, code, name in random.sample(med_tuples[:10], n_items):
                    qty = random.choice([10, 14, 20, 28, 30])
                    dispensed = qty if rx_status == "dispensed" else 0
                    item_st = "dispensed" if dispensed == qty else "pending"
                    await s.execute(text(
                        "INSERT INTO prescription_items (id, fk_prescription_id, fk_medication_id, "
                        "quantity_prescribed, dosage_instructions, duration_days, "
                        "quantity_dispatched, item_status) "
                        "VALUES (:id, :rxid, :mid, :qp, :dose, :dur, :qd, :st)"
                    ), {
                        "id": uid(), "rxid": rx_id, "mid": med_id, "qp": qty,
                        "dose": random.choice(doses),
                        "dur": random.choice([5, 7, 10, 14, 30]),
                        "qd": dispensed, "st": item_st,
                    })
                rx_count += 1
            await s.commit()
            print(f"  + Prescriptions: {rx_count} (with items)")
        else:
            print(f"  = Prescriptions: {existing_rx} already exist")

        # ── 4. Dispatches ─────────────────────────────────────────
        existing_dp = (await fetch_one(s, "SELECT COUNT(*) FROM dispatches"))[0]
        if existing_dp == 0:
            dispensed_rx = await fetch_all(
                s,
                "SELECT id, fk_patient_id FROM prescriptions WHERE prescription_status = 'dispensed'",
            )
            dp_count = 0
            for rx_id, patient_id in dispensed_rx:
                items = await fetch_all(
                    s,
                    "SELECT id, fk_medication_id, quantity_prescribed FROM prescription_items "
                    "WHERE fk_prescription_id = :rxid",
                    {"rxid": rx_id},
                )
                if not items:
                    continue
                dispatch_id = uid()
                dp_date = now - timedelta(days=random.randint(0, 45), hours=random.randint(0, 10))
                ph_id = random.choice(pharmacists) if pharmacists else pharmacist1
                await s.execute(text(
                    "INSERT INTO dispatches (id, fk_prescription_id, fk_patient_id, fk_pharmacist_id, "
                    "dispatch_date, notes, dispatch_status) "
                    "VALUES (:id, :rxid, :pid, :ph, :dt, :n, 'completed')"
                ), {
                    "id": dispatch_id, "rxid": rx_id, "pid": patient_id, "ph": ph_id, "dt": dp_date,
                    "n": random.choice([
                        "Despacho completo. Paciente firmo conformidad.",
                        "Paciente retiro medicamentos personalmente.",
                        "Entregado a familiar autorizado.",
                        "Despacho sin novedades.",
                        None,
                    ]),
                })
                for item_id, med_id, qty in items:
                    batch_match = next(
                        ((b[0], b[3]) for b in batches if b[1] == med_id and b[3] >= qty), None
                    )
                    if not batch_match:
                        continue
                    batch_id, available = batch_match
                    await s.execute(text(
                        "INSERT INTO dispatch_items (id, fk_dispatch_id, fk_batch_id, "
                        "fk_medication_id, quantity_dispatched) "
                        "VALUES (:id, :dpid, :bid, :mid, :qty)"
                    ), {
                        "id": uid(), "dpid": dispatch_id, "bid": batch_id,
                        "mid": med_id, "qty": qty,
                    })
                    await s.execute(text(
                        "UPDATE batches SET quantity_available = quantity_available - :qty WHERE id = :bid"
                    ), {"qty": qty, "bid": batch_id})
                dp_count += 1
            await s.commit()
            print(f"  + Dispatches: {dp_count} (with items)")
        else:
            print(f"  = Dispatches: {existing_dp} already exist")

        # ── 5. Inventory Movements ────────────────────────────────
        existing_mv = (await fetch_one(s, "SELECT COUNT(*) FROM inventory_movements"))[0]
        if existing_mv == 0:
            mv_count = 0
            for batch_id, med_id, lot, _qty in batches[:15]:
                mv_date = now - timedelta(days=random.randint(30, 100))
                qty_in = random.choice([200, 300, 500])
                await s.execute(text(
                    "INSERT INTO inventory_movements (id, fk_medication_id, fk_batch_id, "
                    "movement_type, quantity, balance_after, reference, lot_number, movement_date, notes) "
                    "VALUES (:id, :mid, :bid, 'entry', :qty, :bal, :ref, :lot, :dt, :n)"
                ), {
                    "id": uid(), "mid": med_id, "bid": batch_id,
                    "qty": qty_in, "bal": qty_in,
                    "ref": "PO-2026-0001", "lot": lot, "dt": mv_date,
                    "n": "Entrada por orden de compra",
                })
                mv_count += 1

            dispatch_items = await fetch_all(
                s,
                "SELECT di.fk_medication_id, di.fk_batch_id, di.fk_dispatch_id, "
                "di.quantity_dispatched, b.lot_number "
                "FROM dispatch_items di JOIN batches b ON b.id = di.fk_batch_id LIMIT 30",
            )
            for med_id, batch_id, dp_id, qty, lot in dispatch_items:
                mv_date = now - timedelta(days=random.randint(0, 30))
                bal_r = await fetch_one(s, "SELECT quantity_available FROM batches WHERE id = :bid", {"bid": batch_id})
                balance = bal_r[0] if bal_r else 0
                await s.execute(text(
                    "INSERT INTO inventory_movements (id, fk_medication_id, fk_batch_id, fk_dispatch_id, "
                    "movement_type, quantity, balance_after, reference, lot_number, movement_date, notes) "
                    "VALUES (:id, :mid, :bid, :dpid, 'exit', :qty, :bal, :ref, :lot, :dt, :n)"
                ), {
                    "id": uid(), "mid": med_id, "bid": batch_id, "dpid": dp_id,
                    "qty": qty, "bal": balance, "ref": "Despacho farmacia",
                    "lot": lot, "dt": mv_date, "n": "Salida por despacho de receta",
                })
                mv_count += 1

            for med_id, code, name in random.sample(med_tuples, min(4, len(med_tuples))):
                await s.execute(text(
                    "INSERT INTO inventory_movements (id, fk_medication_id, movement_type, quantity, "
                    "balance_after, reference, movement_date, notes) "
                    "VALUES (:id, :mid, 'adjustment', :qty, :bal, :ref, :dt, :n)"
                ), {
                    "id": uid(), "mid": med_id,
                    "qty": random.choice([-5, -3, -2, 2, 3]),
                    "bal": random.randint(50, 250),
                    "ref": "Conteo fisico mensual",
                    "dt": now - timedelta(days=random.randint(1, 20)),
                    "n": "Ajuste por conteo fisico del inventario",
                })
                mv_count += 1
            await s.commit()
            print(f"  + Inventory Movements: {mv_count}")
        else:
            print(f"  = Inventory Movements: {existing_mv} already exist")

        # ── 6. Stock Alerts ───────────────────────────────────────
        existing_al = (await fetch_one(s, "SELECT COUNT(*) FROM stock_alerts"))[0]
        if existing_al == 0:
            al_count = 0
            low_stock_meds = await fetch_all(
                s,
                "SELECT m.id, m.generic_name, COALESCE(SUM(b.quantity_available), 0) AS total "
                "FROM medications m LEFT JOIN batches b ON b.fk_medication_id = m.id "
                "GROUP BY m.id, m.generic_name ORDER BY total ASC LIMIT 5",
            )
            for med_id, name, total in low_stock_meds:
                level = "critical" if total < 50 else "low"
                threshold = 50 if level == "critical" else 100
                await s.execute(text(
                    "INSERT INTO stock_alerts (id, fk_medication_id, alert_level, current_stock, "
                    "threshold, message, detected_at, alert_status) "
                    "VALUES (:id, :mid, :lvl, :cur, :thr, :msg, :dt, 'active')"
                ), {
                    "id": uid(), "mid": med_id, "lvl": level,
                    "cur": int(total), "thr": threshold,
                    "msg": f"Stock {level} de {name}: {int(total)} unidades restantes",
                    "dt": now - timedelta(hours=random.randint(1, 72)),
                })
                al_count += 1

            if med_tuples:
                med_id, code, name = med_tuples[-1]
                await s.execute(text(
                    "INSERT INTO stock_alerts (id, fk_medication_id, alert_level, current_stock, "
                    "threshold, message, detected_at, resolved_at, alert_status) "
                    "VALUES (:id, :mid, 'expired', 0, 0, :msg, :dt, :rt, 'resolved')"
                ), {
                    "id": uid(), "mid": med_id,
                    "msg": f"Lote expirado de {name} retirado del inventario",
                    "dt": now - timedelta(days=12), "rt": now - timedelta(days=10),
                })
                al_count += 1
            await s.commit()
            print(f"  + Stock Alerts: {al_count}")
        else:
            print(f"  = Stock Alerts: {existing_al} already exist")

        # ── 7. Dispatch Limits ────────────────────────────────────
        existing_lim = (await fetch_one(s, "SELECT COUNT(*) FROM dispatch_limits"))[0]
        if existing_lim == 0:
            lim_count = 0
            limit_defs = [
                (med_tuples[0][0], 60,  "all"),
                (med_tuples[1][0], 30,  "student"),
                (med_tuples[2][0], 90,  "employee"),
                (med_tuples[3][0], 60,  "all"),
                (med_tuples[4][0], 90,  "all"),
            ]
            for med_id, max_qty, applies in limit_defs:
                await s.execute(text(
                    "INSERT INTO dispatch_limits (id, fk_medication_id, monthly_max_quantity, applies_to, active) "
                    "VALUES (:id, :mid, :max, :to, true)"
                ), {"id": uid(), "mid": med_id, "max": max_qty, "to": applies})
                lim_count += 1
            await s.commit()
            print(f"  + Dispatch Limits: {lim_count}")
        else:
            print(f"  = Dispatch Limits: {existing_lim} already exist")

        # ── 8. Dispatch Exceptions ────────────────────────────────
        existing_exc = (await fetch_one(s, "SELECT COUNT(*) FROM dispatch_exceptions"))[0]
        if existing_exc == 0:
            exc_count = 0
            for med_id, code, name in med_tuples[:3]:
                await s.execute(text(
                    "INSERT INTO dispatch_exceptions (id, fk_patient_id, fk_medication_id, "
                    "authorized_quantity, valid_from, valid_until, reason, authorized_by) "
                    "VALUES (:id, :pid, :mid, :qty, :vf, :vu, :r, :by)"
                ), {
                    "id": uid(), "pid": random.choice(patients[:10]),
                    "mid": med_id, "qty": 120,
                    "vf": today, "vu": today + timedelta(days=90),
                    "r": "Tratamiento cronico autorizado por jefatura medica",
                    "by": "Dr. Director Medico CAMIULA",
                })
                exc_count += 1
            await s.commit()
            print(f"  + Dispatch Exceptions: {exc_count}")
        else:
            print(f"  = Dispatch Exceptions: {existing_exc} already exist")

        # ── 9. Medical Records ────────────────────────────────────
        existing_mr = (await fetch_one(s, "SELECT COUNT(*) FROM medical_records"))[0]
        if existing_mr == 0:
            attended_appts = await fetch_all(
                s,
                "SELECT id, fk_patient_id, fk_doctor_id FROM appointments "
                "WHERE appointment_status = 'atendida'",
            )
            mr_count = 0
            diagnoses = [
                ("Gripe comun", "Reposo relativo y tratamiento sintomatico"),
                ("Hipertension arterial leve", "Cambios en estilo de vida, control en 30 dias"),
                ("Diabetes tipo 2 controlada", "Continuar tratamiento, dieta hipoglucida"),
                ("Lumbalgia mecanica", "Fisioterapia y analgesicos segun dolor"),
                ("Gastritis cronica", "Dieta blanda, inhibidores de bomba de protones"),
                ("Infeccion respiratoria alta", "Antibioticoterapia por 7 dias"),
                ("Control general", "Paciente sano, prox control en 6 meses"),
            ]
            vitals = [
                '{"presion": "120/80", "pulso": 72, "temperatura": 36.8, "peso": 70}',
                '{"presion": "130/85", "pulso": 78, "temperatura": 37.1, "peso": 85}',
                '{"presion": "110/70", "pulso": 68, "temperatura": 36.6, "peso": 62}',
                '{"presion": "140/90", "pulso": 80, "temperatura": 36.9, "peso": 90}',
            ]
            for appt_id, patient_id, doctor_id in attended_appts:
                dx, plan = random.choice(diagnoses)
                vt = random.choice(vitals)
                evaluation = (
                    f'{{"motivo_consulta": "Consulta medica", '
                    f'"diagnostico": "{dx}", '
                    f'"plan": "{plan}", '
                    f'"signos_vitales": {vt}}}'
                )
                await s.execute(text(
                    "INSERT INTO medical_records (id, fk_appointment_id, fk_patient_id, fk_doctor_id, "
                    "evaluation, is_prepared, prepared_at, prepared_by) "
                    "VALUES (:id, :aid, :pid, :did, CAST(:ev AS jsonb), true, :pa, :pb)"
                ), {
                    "id": uid(), "aid": appt_id, "pid": patient_id, "did": doctor_id,
                    "ev": evaluation,
                    "pa": now - timedelta(days=random.randint(1, 45)),
                    "pb": doctor_id,
                })
                mr_count += 1
            await s.commit()
            print(f"  + Medical Records: {mr_count}")
        else:
            print(f"  = Medical Records: {existing_mr} already exist")

        # ── 10. Medical Orders ────────────────────────────────────
        existing_mo = (await fetch_one(s, "SELECT COUNT(*) FROM medical_orders"))[0]
        if existing_mo == 0:
            mo_count = 0
            attended_appts = await fetch_all(
                s,
                "SELECT id, fk_patient_id, fk_doctor_id FROM appointments "
                "WHERE appointment_status = 'atendida' LIMIT 12",
            )
            exams = [
                "Hematologia completa",
                "Glicemia en ayunas",
                "Perfil lipidico completo",
                "Urocultivo",
                "Radiografia de torax PA",
                "Electrocardiograma de reposo",
                "Ecografia abdominal",
                "Perfil tiroideo (TSH, T3, T4)",
            ]
            order_statuses = ["requested"] * 3 + ["in_progress"] + ["completed"] * 3
            for appt_id, patient_id, doctor_id in attended_appts:
                n_exams = random.randint(1, 2)
                for exam in random.sample(exams, n_exams):
                    await s.execute(text(
                        "INSERT INTO medical_orders (id, fk_appointment_id, fk_patient_id, fk_doctor_id, "
                        "order_type, exam_name, notes, order_status) "
                        "VALUES (:id, :aid, :pid, :did, 'lab_exam', :exam, :n, :st)"
                    ), {
                        "id": uid(), "aid": appt_id, "pid": patient_id, "did": doctor_id,
                        "exam": exam,
                        "n": "Resultados disponibles en 48-72 horas habiles",
                        "st": random.choice(order_statuses),
                    })
                    mo_count += 1
            await s.commit()
            print(f"  + Medical Orders: {mo_count}")
        else:
            print(f"  = Medical Orders: {existing_mo} already exist")

    await engine.dispose()
    print(f"\nDone. All operational data ready in Supabase.")


if __name__ == "__main__":
    asyncio.run(main())
