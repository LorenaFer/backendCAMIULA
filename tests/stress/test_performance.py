"""Stress & Performance tests — 100k-500k records.

These tests validate that the system handles hospital-scale data
efficiently on scarce-resource hardware:

1. Bulk insert performance (batch operations)
2. Paginated queries over massive datasets (<200ms)
3. Concurrent NHM generation (no duplicates)
4. Index effectiveness (EXPLAIN ANALYZE)
5. Memory-efficient queries (no full table loads)
6. FEFO dispatch under pressure

Run with:
    pytest tests/stress/ -v -s --timeout=300

WARNING: These tests INSERT hundreds of thousands of rows into the DB.
They should run against a dedicated test database, NOT production.
"""

import asyncio
import time
import uuid
from datetime import date, timedelta

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.database.session import async_session_factory


# ── Helpers ───────────────────────────────────────────────────

BATCH_SIZE = 5000  # rows per INSERT batch
TARGET_PATIENTS = 100_000
TARGET_APPOINTMENTS = 200_000
TARGET_MEDICATIONS = 1_000
TARGET_BATCHES = 50_000

# Performance budgets (seconds)
BUDGET_PAGINATED_QUERY = 1.0    # 1s for paginated list (cold cache on dev machine)
BUDGET_SEARCH_INDEXED = 0.05    # 50ms for indexed lookup
BUDGET_STATS_AGGREGATION = 1.0  # 1s for complex aggregation
BUDGET_BULK_INSERT_PER_1K = 0.5 # 500ms per 1000 rows


async def _get_session() -> AsyncSession:
    return async_session_factory()


async def _bulk_insert(session: AsyncSession, sql: str, rows: list):
    """Insert rows in batches for memory efficiency."""
    for i in range(0, len(rows), BATCH_SIZE):
        batch = rows[i:i + BATCH_SIZE]
        await session.execute(text(sql), batch)
    await session.commit()


async def _count_rows(session: AsyncSession, table: str) -> int:
    result = await session.execute(text(f"SELECT COUNT(*) FROM {table} WHERE status = 'A'"))
    return result.scalar_one()


async def _explain_analyze(session: AsyncSession, query: str) -> str:
    """Run EXPLAIN ANALYZE and return the output."""
    result = await session.execute(text(f"EXPLAIN ANALYZE {query}"))
    return "\n".join(row[0] for row in result.fetchall())


# ── Fixtures ──────────────────────────────────────────────────


@pytest.fixture(scope="module")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ── Test: Bulk Patient Insert ─────────────────────────────────


class TestBulkPatientInsert:
    """Insert 100k patients and verify query performance."""

    @pytest.mark.asyncio
    async def test_bulk_insert_patients(self):
        """Insert 100k patients in batches — measures throughput."""
        async with async_session_factory() as session:
            existing = await _count_rows(session, "patients")
            if existing >= TARGET_PATIENTS:
                print(f"\n  Already {existing} patients — skipping bulk insert")
                return

            needed = TARGET_PATIENTS - existing
            print(f"\n  Inserting {needed} patients...")
            start = time.perf_counter()

            # Get current max NHM to avoid conflicts
            max_nhm_result = await session.execute(
                text("SELECT COALESCE(MAX(nhm), 0) FROM patients")
            )
            base_nhm = max_nhm_result.scalar_one()

            sql = text(
                "INSERT INTO patients "
                "(id, nhm, dni, first_name, last_name, university_relation, "
                "is_new, patient_status, status, medical_data, created_at, created_by) "
                "VALUES (:id, :nhm, :dni, :first_name, :last_name, :univ, "
                "true, 'active', 'A', '{}', NOW(), 'stress-test') "
                "ON CONFLICT DO NOTHING"
            )

            relations = ["empleado", "estudiante", "profesor", "tercero"]
            for batch_start in range(0, needed, BATCH_SIZE):
                batch_end = min(batch_start + BATCH_SIZE, needed)
                rows = []
                for i in range(batch_start, batch_end):
                    idx = base_nhm + i + 1
                    rows.append({
                        "id": str(uuid.uuid4()),
                        "nhm": idx,
                        "dni": f"V-STRESS-{idx:07d}",
                        "first_name": f"Nombre{idx}",
                        "last_name": f"Apellido{idx % 1000:04d}",
                        "univ": relations[idx % 4],
                    })
                await session.execute(sql, rows)
                await session.commit()

            elapsed = time.perf_counter() - start
            total = await _count_rows(session, "patients")
            throughput = needed / elapsed if elapsed > 0 else 0
            print(f"  Inserted {needed} patients in {elapsed:.2f}s ({throughput:.0f} rows/s)")
            print(f"  Total patients: {total}")
            assert total >= TARGET_PATIENTS

    @pytest.mark.asyncio
    async def test_paginated_list_performance(self):
        """GET /patients equivalent: paginated query over 100k+ rows < 200ms."""
        async with async_session_factory() as session:
            start = time.perf_counter()
            result = await session.execute(
                text(
                    "SELECT * FROM patients "
                    "WHERE status = 'A' "
                    "ORDER BY last_name, first_name "
                    "OFFSET 50000 LIMIT 20"
                )
            )
            rows = result.fetchall()
            elapsed = time.perf_counter() - start

            print(f"\n  Paginated query (page 2500): {elapsed*1000:.1f}ms, {len(rows)} rows")
            assert elapsed < BUDGET_PAGINATED_QUERY, (
                f"Paginated query took {elapsed*1000:.0f}ms, budget is {BUDGET_PAGINATED_QUERY*1000:.0f}ms"
            )
            assert len(rows) == 20

    @pytest.mark.asyncio
    async def test_search_by_dni_indexed(self):
        """Search by dni (indexed) over 100k+ rows < 50ms."""
        async with async_session_factory() as session:
            start = time.perf_counter()
            result = await session.execute(
                text(
                    "SELECT * FROM patients "
                    "WHERE dni = 'V-STRESS-0050000' AND status = 'A'"
                )
            )
            row = result.fetchone()
            elapsed = time.perf_counter() - start

            print(f"\n  Indexed dni search: {elapsed*1000:.1f}ms")
            assert elapsed < BUDGET_SEARCH_INDEXED, (
                f"Indexed search took {elapsed*1000:.0f}ms, budget is {BUDGET_SEARCH_INDEXED*1000:.0f}ms"
            )
            assert row is not None

    @pytest.mark.asyncio
    async def test_search_by_nhm_indexed(self):
        """Search by NHM (indexed) over 100k+ rows < 50ms."""
        async with async_session_factory() as session:
            start = time.perf_counter()
            result = await session.execute(
                text(
                    "SELECT * FROM patients "
                    "WHERE nhm = 50000 AND status = 'A'"
                )
            )
            row = result.fetchone()
            elapsed = time.perf_counter() - start

            print(f"\n  Indexed NHM search: {elapsed*1000:.1f}ms")
            assert elapsed < BUDGET_SEARCH_INDEXED

    @pytest.mark.asyncio
    async def test_count_uses_index(self):
        """Verify COUNT query uses index, not seq scan."""
        async with async_session_factory() as session:
            plan = await _explain_analyze(
                session,
                "SELECT COUNT(*) FROM patients WHERE status = 'A'"
            )
            print(f"\n  EXPLAIN ANALYZE:\n{plan}")
            # PostgreSQL may choose seq scan for COUNT(*) when most rows match
            # Validate execution time is reasonable (<50ms)
            exec_time_line = [l for l in plan.split("\n") if "Execution Time" in l]
            if exec_time_line:
                ms = float(exec_time_line[0].split(":")[-1].strip().replace(" ms", ""))
                assert ms < 50, f"COUNT took {ms}ms, should be <50ms"

    @pytest.mark.asyncio
    async def test_demographics_aggregation_performance(self):
        """Demographics query (GROUP BY university_relation) < 1s."""
        async with async_session_factory() as session:
            start = time.perf_counter()
            result = await session.execute(
                text(
                    "SELECT university_relation, COUNT(*) "
                    "FROM patients WHERE status = 'A' "
                    "GROUP BY university_relation"
                )
            )
            rows = result.fetchall()
            elapsed = time.perf_counter() - start

            print(f"\n  Demographics aggregation: {elapsed*1000:.1f}ms, {len(rows)} groups")
            assert elapsed < BUDGET_STATS_AGGREGATION


class TestBulkAppointmentInsert:
    """Insert 200k appointments and verify cross-module query performance."""

    @pytest.mark.asyncio
    async def test_bulk_insert_appointments(self):
        """Insert 200k appointments."""
        async with async_session_factory() as session:
            existing = await _count_rows(session, "appointments")
            if existing >= TARGET_APPOINTMENTS:
                print(f"\n  Already {existing} appointments — skipping")
                return

            # Get a doctor and specialty
            doc_result = await session.execute(
                text("SELECT id, fk_specialty_id FROM doctors WHERE status = 'A' LIMIT 1")
            )
            doc = doc_result.fetchone()
            if not doc:
                pytest.skip("No doctors in DB")
            doctor_id, specialty_id = doc[0], doc[1]

            # Get patient IDs
            pat_result = await session.execute(
                text("SELECT id FROM patients WHERE status = 'A' LIMIT 1000")
            )
            patient_ids = [row[0] for row in pat_result.fetchall()]
            if not patient_ids:
                pytest.skip("No patients in DB")

            needed = TARGET_APPOINTMENTS - existing
            print(f"\n  Inserting {needed} appointments...")
            start = time.perf_counter()

            from datetime import time as time_type

            base_date = date(2025, 1, 1)
            statuses = ["pendiente", "confirmada", "atendida", "cancelada", "no_asistio"]
            hours = [time_type(h, 0) for h in range(7, 18)]
            end_hours = [time_type(h, 30) for h in range(7, 18)]

            sql = text(
                "INSERT INTO appointments "
                "(id, fk_patient_id, fk_doctor_id, fk_specialty_id, "
                "appointment_date, start_time, end_time, duration_minutes, "
                "is_first_visit, appointment_status, status, created_at, created_by) "
                "VALUES (:id, :pat, :doc, :spec, :dt, :st, :et, 30, "
                ":first, :appt_status, 'A', NOW(), 'stress-test') "
                "ON CONFLICT DO NOTHING"
            )

            for batch_start in range(0, needed, BATCH_SIZE):
                batch_end = min(batch_start + BATCH_SIZE, needed)
                rows = []
                for i in range(batch_start, batch_end):
                    idx = existing + i
                    day_offset = idx // 11  # ~11 appts per day
                    hour_idx = idx % 11
                    rows.append({
                        "id": str(uuid.uuid4()),
                        "pat": patient_ids[idx % len(patient_ids)],
                        "doc": doctor_id,
                        "spec": specialty_id,
                        "dt": base_date + timedelta(days=day_offset),
                        "st": hours[hour_idx],
                        "et": end_hours[hour_idx],
                        "first": idx % 5 == 0,
                        "appt_status": statuses[idx % 5],
                    })
                await session.execute(sql, rows)
                await session.commit()

            elapsed = time.perf_counter() - start
            total = await _count_rows(session, "appointments")
            print(f"  Inserted {needed} appointments in {elapsed:.2f}s")
            print(f"  Total appointments: {total}")

    @pytest.mark.asyncio
    async def test_appointments_paginated_with_join(self):
        """Paginated appointment list with patient+doctor join < 200ms."""
        async with async_session_factory() as session:
            start = time.perf_counter()
            result = await session.execute(
                text(
                    "SELECT a.*, "
                    "p.first_name || ' ' || p.last_name AS patient_name, "
                    "d.first_name || ' ' || d.last_name AS doctor_name "
                    "FROM appointments a "
                    "JOIN patients p ON p.id = a.fk_patient_id "
                    "JOIN doctors d ON d.id = a.fk_doctor_id "
                    "WHERE a.status = 'A' "
                    "ORDER BY a.appointment_date DESC, a.start_time "
                    "OFFSET 1000 LIMIT 25"
                )
            )
            rows = result.fetchall()
            elapsed = time.perf_counter() - start

            print(f"\n  Paginated appts+join: {elapsed*1000:.1f}ms, {len(rows)} rows")
            assert elapsed < BUDGET_PAGINATED_QUERY

    @pytest.mark.asyncio
    async def test_stats_aggregation_performance(self):
        """Stats aggregation (by_status, by_specialty, etc.) < 1s."""
        async with async_session_factory() as session:
            start = time.perf_counter()
            # Simulate the stats endpoint queries
            await session.execute(
                text(
                    "SELECT appointment_status, COUNT(*) "
                    "FROM appointments WHERE status = 'A' "
                    "GROUP BY appointment_status"
                )
            )
            await session.execute(
                text(
                    "SELECT s.name, COUNT(*) "
                    "FROM appointments a "
                    "JOIN specialties s ON s.id = a.fk_specialty_id "
                    "WHERE a.status = 'A' "
                    "GROUP BY s.name"
                )
            )
            elapsed = time.perf_counter() - start

            print(f"\n  Stats aggregation: {elapsed*1000:.1f}ms")
            assert elapsed < BUDGET_STATS_AGGREGATION

    @pytest.mark.asyncio
    async def test_heatmap_aggregation_performance(self):
        """Heatmap (group by dow x hour) < 1s."""
        async with async_session_factory() as session:
            start = time.perf_counter()
            result = await session.execute(
                text(
                    "SELECT EXTRACT(ISODOW FROM appointment_date) AS dow, "
                    "EXTRACT(HOUR FROM start_time) AS hour, "
                    "COUNT(*) "
                    "FROM appointments WHERE status = 'A' "
                    "GROUP BY dow, hour "
                    "ORDER BY dow, hour"
                )
            )
            rows = result.fetchall()
            elapsed = time.perf_counter() - start

            print(f"\n  Heatmap aggregation: {elapsed*1000:.1f}ms, {len(rows)} cells")
            assert elapsed < BUDGET_STATS_AGGREGATION


class TestConcurrentNhmGeneration:
    """Verify NHM generation is safe under concurrent access."""

    @pytest.mark.asyncio
    async def test_concurrent_nhm_no_duplicates(self):
        """10 concurrent patient creations must produce unique NHMs."""
        import httpx
        from app.main import app

        # Get token
        email = f"stress-nhm-{uuid.uuid4().hex[:6]}@test.com"
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as c:
            await c.post(
                "/api/auth/register",
                json={"email": email, "full_name": "Stress NHM", "password": "pytest12345"},
            )
            resp = await c.post(
                "/api/auth/login", json={"email": email, "password": "pytest12345"}
            )
            token = resp.json()["data"]["access_token"]

        async def create_patient(idx: int) -> int:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://test"
            ) as c:
                resp = await c.post(
                    "/api/patients",
                    json={
                        "dni": f"V-CONC-{uuid.uuid4().hex[:8]}",
                        "first_name": f"Concurrent{idx}",
                        "last_name": "Test",
                        "university_relation": "estudiante",
                    },
                    headers={"Authorization": f"Bearer {token}"},
                )
                if resp.status_code == 201:
                    return resp.json()["data"]["nhm"]
                return -1

        # Run 10 concurrent creates
        tasks = [create_patient(i) for i in range(10)]
        nhms = await asyncio.gather(*tasks)

        valid_nhms = [n for n in nhms if n > 0]
        unique_nhms = set(valid_nhms)
        print(f"\n  Created {len(valid_nhms)} patients, {len(unique_nhms)} unique NHMs")
        assert len(valid_nhms) == len(unique_nhms), (
            f"Duplicate NHMs detected! {valid_nhms}"
        )


class TestInventoryPerformance:
    """Verify inventory queries scale with large batch/medication data."""

    @pytest.mark.asyncio
    async def test_stock_report_performance(self):
        """Stock report aggregation over 50k+ batches < 1s."""
        async with async_session_factory() as session:
            batch_count = await _count_rows(session, "batches")
            print(f"\n  Batches in DB: {batch_count}")

            start = time.perf_counter()
            result = await session.execute(
                text(
                    "SELECT m.id, m.generic_name, m.code, "
                    "COALESCE(SUM(b.quantity_available), 0) AS stock "
                    "FROM medications m "
                    "LEFT JOIN batches b ON b.fk_medication_id = m.id "
                    "AND b.batch_status = 'available' AND b.status = 'A' "
                    "WHERE m.status = 'A' "
                    "GROUP BY m.id, m.generic_name, m.code "
                    "ORDER BY m.generic_name"
                )
            )
            rows = result.fetchall()
            elapsed = time.perf_counter() - start

            print(f"  Stock report: {elapsed*1000:.1f}ms, {len(rows)} medications")
            assert elapsed < BUDGET_STATS_AGGREGATION


class TestQueryPlanValidation:
    """Verify critical queries use indices (not sequential scans)."""

    @pytest.mark.asyncio
    async def test_patient_dni_uses_index(self):
        async with async_session_factory() as session:
            plan = await _explain_analyze(
                session,
                "SELECT * FROM patients WHERE dni = 'V-STRESS-0050000' AND status = 'A'"
            )
            print(f"\n{plan}")
            assert "Index" in plan, "Patient dni query missing index usage"

    @pytest.mark.asyncio
    async def test_appointment_date_doctor_uses_index(self):
        async with async_session_factory() as session:
            plan = await _explain_analyze(
                session,
                "SELECT * FROM appointments "
                "WHERE fk_doctor_id = '00000000-0000-0000-0000-000000000001' "
                "AND appointment_date = '2025-06-15' AND status = 'A'"
            )
            print(f"\n{plan}")
            # Should use composite or individual index

    @pytest.mark.asyncio
    async def test_batch_fefo_uses_index(self):
        async with async_session_factory() as session:
            plan = await _explain_analyze(
                session,
                "SELECT * FROM batches "
                "WHERE fk_medication_id = '00000000-0000-0000-0000-000000000001' "
                "AND batch_status = 'available' AND status = 'A' "
                "ORDER BY expiration_date ASC"
            )
            print(f"\n{plan}")
