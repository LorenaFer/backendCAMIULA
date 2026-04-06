"""Integration tests for Appointment endpoints.

Each test exercises the full HTTP endpoint (router -> use case -> repo -> DB).
Uses httpx.AsyncClient against the real FastAPI app with the test DB.
"""

import random
import uuid

import httpx
import pytest
import pytest_asyncio

from app.main import app

BASE = "/api/appointments"


async def _get_token() -> str:
    """Gets a valid JWT token for authenticated requests."""
    email = f"pytest-appts-{uuid.uuid4().hex[:6]}@test.com"
    password = "pytest12345"
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as c:
        await c.post(
            "/api/auth/register",
            json={
                "email": email,
                "full_name": "Pytest Appts Tester",
                "password": password,
            },
        )
        resp = await c.post(
            "/api/auth/login", json={"email": email, "password": password}
        )
        assert resp.status_code == 200, f"Login failed: {resp.text}"
        return resp.json()["data"]["access_token"]


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _unique_cedula() -> str:
    return f"V-APPT-{uuid.uuid4().hex[:8]}"


async def _create_patient(client, token: str) -> str:
    """Create a patient and return its ID."""
    cedula = _unique_cedula()
    resp = await client.post(
        "/api/patients",
        json={
            "cedula": cedula,
            "first_name": "TestPaciente",
            "last_name": "ApptTest",
            "university_relation": "estudiante",
        },
        headers=_auth_headers(token),
    )
    assert resp.status_code == 201, f"Create patient failed: {resp.text}"
    return resp.json()["data"]["id"]


async def _get_doctor_and_specialty(client, token: str):
    """Get an existing doctor ID and specialty ID, or return (None, None)."""
    resp = await client.get("/api/doctors", headers=_auth_headers(token))
    assert resp.status_code == 200
    doctors = resp.json()["data"]
    if not doctors:
        return None, None
    doc = doctors[0]
    return doc["id"], doc["fk_specialty_id"]


async def _create_specialty(client, token: str) -> str:
    """Create a specialty and return its ID."""
    name = f"Spec-{uuid.uuid4().hex[:6]}"
    resp = await client.post(
        "/api/specialties",
        json={"name": name},
        headers=_auth_headers(token),
    )
    assert resp.status_code == 201, f"Create specialty failed: {resp.text}"
    return resp.json()["data"]["id"]


@pytest.fixture(scope="module")
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture
async def token():
    return await _get_token()


@pytest_asyncio.fixture
async def client():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c


class TestCreateAppointment:
    """POST /api/appointments"""

    @pytest.mark.asyncio
    async def test_create_appointment_success(self, client, token):
        patient_id = await _create_patient(client, token)
        doctor_id, specialty_id = await _get_doctor_and_specialty(client, token)
        if not doctor_id:
            specialty_id = await _create_specialty(client, token)
            pytest.skip("No doctors seeded in test DB — cannot test create")

        unique_time = f"{9:02d}:{uuid.uuid4().int % 60:02d}"
        resp = await client.post(
            BASE,
            json={
                "fk_patient_id": patient_id,
                "fk_doctor_id": doctor_id,
                "fk_specialty_id": specialty_id,
                "appointment_date": "2026-06-15",
                "start_time": unique_time,
                "end_time": "10:00",
                "duration_minutes": 30,
                "is_first_visit": True,
                "reason": "Consulta general",
            },
            headers=_auth_headers(token),
        )
        assert resp.status_code == 201, f"Create failed: {resp.text}"
        body = resp.json()
        assert body["status"] == "success"
        assert body["data"]["appointment_status"] == "pendiente"
        assert body["data"]["is_first_visit"] is True

    @pytest.mark.asyncio
    async def test_create_appointment_double_booking(self, client, token):
        patient_id = await _create_patient(client, token)
        doctor_id, specialty_id = await _get_doctor_and_specialty(client, token)
        if not doctor_id:
            pytest.skip("No doctors seeded in test DB")

        # Use a random future date + unique minute to avoid collisions with other runs
        rand_day = random.randint(1, 28)
        rand_min = random.randint(0, 59)
        unique_date = f"2027-{random.randint(1,12):02d}-{rand_day:02d}"
        unique_time = f"14:{rand_min:02d}"
        payload = {
            "fk_patient_id": patient_id,
            "fk_doctor_id": doctor_id,
            "fk_specialty_id": specialty_id,
            "appointment_date": unique_date,
            "start_time": unique_time,
            "end_time": "15:00",
            "duration_minutes": 30,
        }
        resp1 = await client.post(
            BASE, json=payload, headers=_auth_headers(token)
        )
        assert resp1.status_code == 201, f"First create failed: {resp1.text}"

        resp2 = await client.post(
            BASE, json=payload, headers=_auth_headers(token)
        )
        assert resp2.status_code == 409
        assert "ya existe" in resp2.json()["message"].lower()

    @pytest.mark.asyncio
    async def test_create_appointment_missing_fields(self, client, token):
        resp = await client.post(
            BASE,
            json={"fk_patient_id": "abc"},
            headers=_auth_headers(token),
        )
        assert resp.status_code == 422


class TestListAppointments:
    """GET /api/appointments"""

    @pytest.mark.asyncio
    async def test_list_paginated(self, client, token):
        resp = await client.get(
            f"{BASE}?page=1&page_size=5", headers=_auth_headers(token)
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body["data"]
        assert "pagination" in body["data"]
        assert body["data"]["pagination"]["page"] == 1


class TestGetAppointment:
    """GET /api/appointments/{id}"""

    @pytest.mark.asyncio
    async def test_get_not_found(self, client, token):
        fake_id = str(uuid.uuid4())
        resp = await client.get(
            f"{BASE}/{fake_id}", headers=_auth_headers(token)
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_get_appointment_detail(self, client, token):
        patient_id = await _create_patient(client, token)
        doctor_id, specialty_id = await _get_doctor_and_specialty(client, token)
        if not doctor_id:
            pytest.skip("No doctors seeded in test DB")

        rand_min = random.randint(0, 59)
        create_resp = await client.post(
            BASE,
            json={
                "fk_patient_id": patient_id,
                "fk_doctor_id": doctor_id,
                "fk_specialty_id": specialty_id,
                "appointment_date": f"2028-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
                "start_time": f"11:{rand_min:02d}",
                "end_time": "12:00",
                "duration_minutes": 30,
            },
            headers=_auth_headers(token),
        )
        assert create_resp.status_code == 201, f"Create failed: {create_resp.text}"
        appt_id = create_resp.json()["data"]["id"]

        resp = await client.get(
            f"{BASE}/{appt_id}", headers=_auth_headers(token)
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["id"] == appt_id
        assert data["patient_name"] is not None
        assert data["doctor_name"] is not None


class TestUpdateStatus:
    """PATCH /api/appointments/{id}/status"""

    @pytest.mark.asyncio
    async def test_state_machine_valid(self, client, token):
        patient_id = await _create_patient(client, token)
        doctor_id, specialty_id = await _get_doctor_and_specialty(client, token)
        if not doctor_id:
            pytest.skip("No doctors seeded in test DB")

        rand_min = random.randint(0, 59)
        create_resp = await client.post(
            BASE,
            json={
                "fk_patient_id": patient_id,
                "fk_doctor_id": doctor_id,
                "fk_specialty_id": specialty_id,
                "appointment_date": f"2029-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
                "start_time": f"08:{rand_min:02d}",
                "end_time": "09:00",
                "duration_minutes": 30,
            },
            headers=_auth_headers(token),
        )
        assert create_resp.status_code == 201, f"Create failed: {create_resp.text}"
        appt_id = create_resp.json()["data"]["id"]

        # pendiente -> confirmada
        resp = await client.patch(
            f"{BASE}/{appt_id}/status",
            json={"new_status": "confirmada"},
            headers=_auth_headers(token),
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["appointment_status"] == "confirmada"

        # confirmada -> atendida
        resp = await client.patch(
            f"{BASE}/{appt_id}/status",
            json={"new_status": "atendida"},
            headers=_auth_headers(token),
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["appointment_status"] == "atendida"

    @pytest.mark.asyncio
    async def test_state_machine_invalid(self, client, token):
        patient_id = await _create_patient(client, token)
        doctor_id, specialty_id = await _get_doctor_and_specialty(client, token)
        if not doctor_id:
            pytest.skip("No doctors seeded in test DB")

        rand_min = random.randint(0, 59)
        create_resp = await client.post(
            BASE,
            json={
                "fk_patient_id": patient_id,
                "fk_doctor_id": doctor_id,
                "fk_specialty_id": specialty_id,
                "appointment_date": f"2030-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
                "start_time": f"09:{rand_min:02d}",
                "end_time": "10:00",
                "duration_minutes": 30,
            },
            headers=_auth_headers(token),
        )
        assert create_resp.status_code == 201, f"Create failed: {create_resp.text}"
        appt_id = create_resp.json()["data"]["id"]

        # pendiente -> atendida (invalid)
        resp = await client.patch(
            f"{BASE}/{appt_id}/status",
            json={"new_status": "atendida"},
            headers=_auth_headers(token),
        )
        assert resp.status_code == 400
        assert "transicion invalida" in resp.json()["message"].lower()


class TestStats:
    """GET /api/appointments/stats"""

    @pytest.mark.asyncio
    async def test_stats_endpoint(self, client, token):
        resp = await client.get(
            f"{BASE}/stats", headers=_auth_headers(token)
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "total" in data
        assert "by_status" in data
        assert "by_specialty" in data
        assert "by_doctor" in data
        assert "first_time_count" in data
        assert "returning_count" in data
        assert "by_patient_type" in data
        assert "daily_trend" in data
        assert "peak_hours" in data


class TestCheckSlot:
    """GET /api/appointments/check-slot"""

    @pytest.mark.asyncio
    async def test_check_slot_free(self, client, token):
        fake_doctor = str(uuid.uuid4())
        resp = await client.get(
            f"{BASE}/check-slot?doctor_id={fake_doctor}&date_str=2026-12-01&hora_inicio=10:00",
            headers=_auth_headers(token),
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["occupied"] is False


class TestAvailableSlots:
    """GET /api/appointments/available-slots"""

    @pytest.mark.asyncio
    async def test_available_slots_no_availability(self, client, token):
        fake_doctor = str(uuid.uuid4())
        resp = await client.get(
            f"{BASE}/available-slots?doctor_id={fake_doctor}&date_str=2026-12-01&es_nuevo=false",
            headers=_auth_headers(token),
        )
        assert resp.status_code == 200
        assert resp.json()["data"] == []


class TestAvailableDates:
    """GET /api/appointments/available-dates"""

    @pytest.mark.asyncio
    async def test_available_dates_no_availability(self, client, token):
        fake_doctor = str(uuid.uuid4())
        resp = await client.get(
            f"{BASE}/available-dates?doctor_id={fake_doctor}&year=2026&month=12",
            headers=_auth_headers(token),
        )
        assert resp.status_code == 200
        assert resp.json()["data"] == []


class TestUnauthenticated:
    """Public GET endpoints return 200 without token; POST still requires auth."""

    @pytest.mark.asyncio
    async def test_list_without_token(self, client):
        resp = await client.get(BASE)
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_create_without_token_no_auth_block(self, client):
        """POST /appointments is public for portal — missing fields give 422, not 403."""
        resp = await client.post(BASE, json={})
        # Without required fields → 422 (validation error), NOT 403 (auth)
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_stats_without_token(self, client):
        resp = await client.get(f"{BASE}/stats")
        assert resp.status_code == 200
