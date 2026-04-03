"""Integration tests for Medical Records endpoints.

Each test exercises the full HTTP endpoint (router -> use case -> repo -> DB).
Uses httpx.AsyncClient against the real FastAPI app with the test DB.
"""

import random
import uuid

import httpx
import pytest
import pytest_asyncio

from app.main import app

BASE_RECORDS = "/api/medical-records"
BASE_SCHEMAS = "/api/schemas"


async def _get_token() -> str:
    """Gets a valid JWT token for authenticated requests."""
    email = f"pytest-medrec-{uuid.uuid4().hex[:6]}@test.com"
    password = "pytest12345"
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as c:
        await c.post(
            "/api/auth/register",
            json={
                "email": email,
                "full_name": "Pytest MedRec",
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


def _unique_id() -> str:
    return str(uuid.uuid4())


async def _create_appointment(client, token: str) -> dict:
    """Create a real patient + appointment for medical record tests."""
    headers = _auth_headers(token)
    # Create patient
    cedula = f"V-MR-{uuid.uuid4().hex[:8]}"
    pat_resp = await client.post(
        "/api/patients",
        json={
            "cedula": cedula,
            "first_name": "MRTest",
            "last_name": "Patient",
            "university_relation": "estudiante",
        },
        headers=headers,
    )
    assert pat_resp.status_code == 201, f"Create patient failed: {pat_resp.text}"
    patient_id = pat_resp.json()["data"]["id"]

    # Get a doctor
    doc_resp = await client.get("/api/doctors", headers=headers)
    doctors = doc_resp.json()["data"]
    if not doctors:
        pytest.skip("No doctors seeded in test DB")
    doctor_id = doctors[0]["id"]
    specialty_id = doctors[0]["fk_specialty_id"]

    # Create appointment
    rand_min = random.randint(0, 59)
    appt_resp = await client.post(
        "/api/appointments",
        json={
            "fk_patient_id": patient_id,
            "fk_doctor_id": doctor_id,
            "fk_specialty_id": specialty_id,
            "appointment_date": f"2031-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
            "start_time": f"10:{rand_min:02d}",
            "end_time": "11:00",
            "duration_minutes": 30,
            "is_first_visit": True,
        },
        headers=headers,
    )
    assert appt_resp.status_code == 201, f"Create appointment failed: {appt_resp.text}"
    appt = appt_resp.json()["data"]
    return {
        "appointment_id": appt["id"],
        "patient_id": patient_id,
        "doctor_id": doctor_id,
    }


# ──────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────


@pytest.fixture(scope="function")
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture(scope="function")
async def client():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c


@pytest_asyncio.fixture(scope="function")
async def token():
    return await _get_token()


# ──────────────────────────────────────────────────────────────
# Medical Records Tests
# ──────────────────────────────────────────────────────────────


@pytest.mark.anyio
async def test_upsert_creates_medical_record(client, token):
    """PUT /medical-records creates a new record when none exists."""
    ctx = await _create_appointment(client, token)

    resp = await client.put(
        BASE_RECORDS,
        json={
            "fk_appointment_id": ctx["appointment_id"],
            "fk_patient_id": ctx["patient_id"],
            "fk_doctor_id": ctx["doctor_id"],
            "evaluation": {"diagnosis": {"description": "Healthy", "code": "Z00"}},
        },
        headers=_auth_headers(token),
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()["data"]
    assert data["fk_appointment_id"] == ctx["appointment_id"]
    assert data["is_prepared"] is False


@pytest.mark.anyio
async def test_upsert_updates_existing_record(client, token):
    """PUT /medical-records updates when record already exists for appointment."""
    ctx = await _create_appointment(client, token)
    appointment_id = ctx["appointment_id"]
    patient_id = ctx["patient_id"]
    doctor_id = ctx["doctor_id"]

    # Create
    resp1 = await client.put(
        BASE_RECORDS,
        json={
            "fk_appointment_id": appointment_id,
            "fk_patient_id": patient_id,
            "fk_doctor_id": doctor_id,
            "evaluation": {"notes": "initial"},
        },
        headers=_auth_headers(token),
    )
    assert resp1.status_code == 201

    # Update
    resp2 = await client.put(
        BASE_RECORDS,
        json={
            "fk_appointment_id": appointment_id,
            "fk_patient_id": patient_id,
            "fk_doctor_id": doctor_id,
            "evaluation": {"notes": "updated"},
        },
        headers=_auth_headers(token),
    )
    assert resp2.status_code == 200, resp2.text
    data = resp2.json()["data"]
    assert data["evaluation"]["notes"] == "updated"


@pytest.mark.anyio
async def test_find_by_appointment(client, token):
    """GET /medical-records?appointment_id=X returns the record."""
    ctx = await _create_appointment(client, token)

    await client.put(
        BASE_RECORDS,
        json={
            "fk_appointment_id": ctx["appointment_id"],
            "fk_patient_id": ctx["patient_id"],
            "fk_doctor_id": ctx["doctor_id"],
        },
        headers=_auth_headers(token),
    )

    resp = await client.get(
        f"{BASE_RECORDS}?appointment_id={ctx['appointment_id']}",
        headers=_auth_headers(token),
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["fk_appointment_id"] == ctx["appointment_id"]


@pytest.mark.anyio
async def test_find_by_appointment_not_found(client, token):
    """GET /medical-records?appointment_id=X returns 404 when not found."""
    resp = await client.get(
        f"{BASE_RECORDS}?appointment_id={_unique_id()}",
        headers=_auth_headers(token),
    )
    assert resp.status_code == 404


@pytest.mark.anyio
async def test_find_by_id(client, token):
    """GET /medical-records/{id} returns the record."""
    ctx = await _create_appointment(client, token)

    create_resp = await client.put(
        BASE_RECORDS,
        json={
            "fk_appointment_id": ctx["appointment_id"],
            "fk_patient_id": ctx["patient_id"],
            "fk_doctor_id": ctx["doctor_id"],
        },
        headers=_auth_headers(token),
    )
    assert create_resp.status_code == 201, create_resp.text
    record_id = create_resp.json()["data"]["id"]

    resp = await client.get(
        f"{BASE_RECORDS}/{record_id}",
        headers=_auth_headers(token),
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["id"] == record_id


@pytest.mark.anyio
async def test_find_by_id_not_found(client, token):
    """GET /medical-records/{id} returns 404 for non-existent ID."""
    resp = await client.get(
        f"{BASE_RECORDS}/{_unique_id()}",
        headers=_auth_headers(token),
    )
    assert resp.status_code == 404


@pytest.mark.anyio
async def test_mark_prepared(client, token):
    """PATCH /medical-records/{id}/prepared marks the record."""
    ctx = await _create_appointment(client, token)
    preparer_id = _unique_id()

    create_resp = await client.put(
        BASE_RECORDS,
        json={
            "fk_appointment_id": ctx["appointment_id"],
            "fk_patient_id": ctx["patient_id"],
            "fk_doctor_id": ctx["doctor_id"],
        },
        headers=_auth_headers(token),
    )
    assert create_resp.status_code == 201, create_resp.text
    record_id = create_resp.json()["data"]["id"]

    resp = await client.patch(
        f"{BASE_RECORDS}/{record_id}/prepared",
        json={"prepared_by": preparer_id},
        headers=_auth_headers(token),
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["is_prepared"] is True
    assert data["prepared_by"] == preparer_id
    assert data["prepared_at"] is not None


@pytest.mark.anyio
async def test_mark_prepared_not_found(client, token):
    """PATCH /medical-records/{id}/prepared returns 404 for non-existent."""
    resp = await client.patch(
        f"{BASE_RECORDS}/{_unique_id()}/prepared",
        json={"prepared_by": _unique_id()},
        headers=_auth_headers(token),
    )
    assert resp.status_code == 404


# ──────────────────────────────────────────────────────────────
# Form Schema Tests
# ──────────────────────────────────────────────────────────────


@pytest.mark.anyio
async def test_upsert_creates_schema(client, token):
    """PUT /schemas creates a new form schema."""
    specialty_id = _unique_id()
    suffix = random.randint(1000, 9999)

    resp = await client.put(
        BASE_SCHEMAS,
        json={
            "specialty_id": specialty_id,
            "specialty_name": f"Test Specialty {suffix}",
            "version": "1.0",
            "schema_json": {"sections": []},
        },
        headers=_auth_headers(token),
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()["data"]
    assert data["specialty_id"] == specialty_id
    assert data["version"] == "1.0"


@pytest.mark.anyio
async def test_upsert_updates_schema(client, token):
    """PUT /schemas updates existing schema for same specialty_id."""
    specialty_id = _unique_id()
    suffix = random.randint(1000, 9999)

    # Create
    await client.put(
        BASE_SCHEMAS,
        json={
            "specialty_id": specialty_id,
            "specialty_name": f"Spec {suffix}",
            "version": "1.0",
            "schema_json": {"sections": []},
        },
        headers=_auth_headers(token),
    )

    # Update
    resp = await client.put(
        BASE_SCHEMAS,
        json={
            "specialty_id": specialty_id,
            "specialty_name": f"Spec {suffix}",
            "version": "2.0",
            "schema_json": {"sections": [{"title": "Vitals"}]},
        },
        headers=_auth_headers(token),
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"]["version"] == "2.0"


@pytest.mark.anyio
async def test_list_schemas(client, token):
    """GET /schemas returns all active schemas."""
    resp = await client.get(BASE_SCHEMAS, headers=_auth_headers(token))
    assert resp.status_code == 200
    assert isinstance(resp.json()["data"], list)


@pytest.mark.anyio
async def test_get_schema_by_specialty_id(client, token):
    """GET /schemas/{specialty_id} finds by UUID."""
    specialty_id = _unique_id()
    suffix = random.randint(1000, 9999)

    await client.put(
        BASE_SCHEMAS,
        json={
            "specialty_id": specialty_id,
            "specialty_name": f"Cardiology {suffix}",
            "version": "1.0",
            "schema_json": {"sections": []},
        },
        headers=_auth_headers(token),
    )

    resp = await client.get(
        f"{BASE_SCHEMAS}/{specialty_id}",
        headers=_auth_headers(token),
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["specialty_id"] == specialty_id


@pytest.mark.anyio
async def test_get_schema_by_normalized_name(client, token):
    """GET /schemas/{name} finds by normalized specialty name."""
    specialty_id = _unique_id()
    suffix = random.randint(1000, 9999)
    name = f"Medicina General {suffix}"

    await client.put(
        BASE_SCHEMAS,
        json={
            "specialty_id": specialty_id,
            "specialty_name": name,
            "version": "1.0",
            "schema_json": {"sections": []},
        },
        headers=_auth_headers(token),
    )

    normalized = name.lower().replace(" ", "-")
    resp = await client.get(
        f"{BASE_SCHEMAS}/{normalized}",
        headers=_auth_headers(token),
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["specialty_id"] == specialty_id


@pytest.mark.anyio
async def test_get_schema_not_found(client, token):
    """GET /schemas/{key} returns 404 for non-existent."""
    resp = await client.get(
        f"{BASE_SCHEMAS}/nonexistent-specialty",
        headers=_auth_headers(token),
    )
    assert resp.status_code == 404


@pytest.mark.anyio
async def test_delete_schema(client, token):
    """DELETE /schemas/{specialty_key} soft-deletes by normalized name."""
    specialty_id = _unique_id()
    suffix = random.randint(1000, 9999)
    name = f"Dermatologia {suffix}"

    await client.put(
        BASE_SCHEMAS,
        json={
            "specialty_id": specialty_id,
            "specialty_name": name,
            "version": "1.0",
            "schema_json": {"sections": []},
        },
        headers=_auth_headers(token),
    )

    normalized = name.lower().replace(" ", "-")
    resp = await client.delete(
        f"{BASE_SCHEMAS}/{normalized}",
        headers=_auth_headers(token),
    )
    assert resp.status_code == 200

    # Verify it's gone
    resp2 = await client.get(
        f"{BASE_SCHEMAS}/{specialty_id}",
        headers=_auth_headers(token),
    )
    assert resp2.status_code == 404


@pytest.mark.anyio
async def test_delete_schema_not_found(client, token):
    """DELETE /schemas/{key} returns 404 for non-existent."""
    resp = await client.delete(
        f"{BASE_SCHEMAS}/nonexistent-{random.randint(1000, 9999)}",
        headers=_auth_headers(token),
    )
    assert resp.status_code == 404


# ──────────────────────────────────────────────────────────────
# Auth guard tests
# ──────────────────────────────────────────────────────────────


@pytest.mark.anyio
async def test_endpoints_require_auth(client):
    """All endpoints return 401/403 without a token."""
    endpoints = [
        ("GET", f"{BASE_RECORDS}?appointment_id=x"),
        ("GET", f"{BASE_RECORDS}/{_unique_id()}"),
        ("PUT", BASE_RECORDS),
        ("GET", f"{BASE_RECORDS}/patient/{_unique_id()}"),
        ("PATCH", f"{BASE_RECORDS}/{_unique_id()}/prepared"),
        ("GET", BASE_SCHEMAS),
        ("GET", f"{BASE_SCHEMAS}/some-key"),
        ("PUT", BASE_SCHEMAS),
        ("DELETE", f"{BASE_SCHEMAS}/some-key"),
    ]
    for method, url in endpoints:
        resp = await client.request(method, url)
        assert resp.status_code in (401, 403), (
            f"{method} {url} should require auth, got {resp.status_code}"
        )
