"""Integration tests for Doctors module endpoints.

Exercises the full HTTP stack: router -> use case -> repo -> DB.
Uses httpx.AsyncClient against the real FastAPI app with the test DB.
"""

import uuid

import httpx
import pytest
import pytest_asyncio

from app.main import app

SPECIALTIES_BASE = "/api/specialties"
DOCTORS_BASE = "/api/doctors"


async def _get_token() -> str:
    """Gets a valid JWT token for authenticated requests."""
    email = f"pytest-doctors-{uuid.uuid4().hex[:6]}@test.com"
    password = "pytest12345"
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as c:
        await c.post(
            "/api/auth/register",
            json={
                "email": email,
                "full_name": "Pytest Doctor Tester",
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


# ─────────────────────────────────────────────────────────────
# SPECIALTIES
# ─────────────────────────────────────────────────────────────


class TestListSpecialties:
    """GET /api/specialties"""

    @pytest.mark.asyncio
    async def test_list_specialties(self, client, token):
        resp = await client.get(SPECIALTIES_BASE, headers=_auth_headers(token))
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "success"
        assert isinstance(body["data"], list)


class TestCreateSpecialty:
    """POST /api/specialties"""

    @pytest.mark.asyncio
    async def test_create_specialty_success(self, client, token):
        name = f"Specialty-{uuid.uuid4().hex[:8]}"
        resp = await client.post(
            SPECIALTIES_BASE,
            json={"name": name},
            headers=_auth_headers(token),
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["status"] == "success"
        assert body["data"]["name"] == name
        assert body["data"]["id"] is not None

    @pytest.mark.asyncio
    async def test_create_specialty_duplicate(self, client, token):
        name = f"Specialty-{uuid.uuid4().hex[:8]}"
        await client.post(
            SPECIALTIES_BASE,
            json={"name": name},
            headers=_auth_headers(token),
        )
        resp = await client.post(
            SPECIALTIES_BASE,
            json={"name": name},
            headers=_auth_headers(token),
        )
        assert resp.status_code == 409

    @pytest.mark.asyncio
    async def test_create_specialty_missing_name(self, client, token):
        resp = await client.post(
            SPECIALTIES_BASE,
            json={},
            headers=_auth_headers(token),
        )
        assert resp.status_code == 422


class TestUpdateSpecialty:
    """PUT /api/specialties/{id}"""

    @pytest.mark.asyncio
    async def test_update_specialty(self, client, token):
        name = f"Specialty-{uuid.uuid4().hex[:8]}"
        create_resp = await client.post(
            SPECIALTIES_BASE,
            json={"name": name},
            headers=_auth_headers(token),
        )
        specialty_id = create_resp.json()["data"]["id"]

        new_name = f"Updated-{uuid.uuid4().hex[:8]}"
        resp = await client.put(
            f"{SPECIALTIES_BASE}/{specialty_id}",
            json={"name": new_name},
            headers=_auth_headers(token),
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["name"] == new_name

    @pytest.mark.asyncio
    async def test_update_specialty_not_found(self, client, token):
        resp = await client.put(
            f"{SPECIALTIES_BASE}/{uuid.uuid4()}",
            json={"name": "Nonexistent"},
            headers=_auth_headers(token),
        )
        assert resp.status_code == 404


class TestToggleSpecialty:
    """PATCH /api/specialties/{id}/toggle"""

    @pytest.mark.asyncio
    async def test_toggle_specialty(self, client, token):
        name = f"Specialty-{uuid.uuid4().hex[:8]}"
        create_resp = await client.post(
            SPECIALTIES_BASE,
            json={"name": name},
            headers=_auth_headers(token),
        )
        specialty_id = create_resp.json()["data"]["id"]
        original_status = create_resp.json()["data"]["status"]

        resp = await client.patch(
            f"{SPECIALTIES_BASE}/{specialty_id}/toggle",
            headers=_auth_headers(token),
        )
        assert resp.status_code == 200
        new_status = resp.json()["data"]["status"]
        assert new_status != original_status

        # Toggle back
        resp2 = await client.patch(
            f"{SPECIALTIES_BASE}/{specialty_id}/toggle",
            headers=_auth_headers(token),
        )
        assert resp2.status_code == 200
        assert resp2.json()["data"]["status"] == original_status

    @pytest.mark.asyncio
    async def test_toggle_specialty_not_found(self, client, token):
        resp = await client.patch(
            f"{SPECIALTIES_BASE}/{uuid.uuid4()}/toggle",
            headers=_auth_headers(token),
        )
        assert resp.status_code == 404


# ─────────────────────────────────────────────────────────────
# DOCTORS
# ─────────────────────────────────────────────────────────────


class TestListDoctors:
    """GET /api/doctors"""

    @pytest.mark.asyncio
    async def test_list_doctors(self, client, token):
        resp = await client.get(DOCTORS_BASE, headers=_auth_headers(token))
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "success"
        assert isinstance(body["data"], list)


class TestDoctorOptions:
    """GET /api/doctors/options"""

    @pytest.mark.asyncio
    async def test_doctor_options(self, client, token):
        resp = await client.get(
            f"{DOCTORS_BASE}/options", headers=_auth_headers(token)
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "success"
        assert isinstance(body["data"], list)


# ─────────────────────────────────────────────────────────────
# AVAILABILITY — requires a doctor in DB; tests run against
# a freshly-seeded or empty DB so we test the happy-path shape.
# ─────────────────────────────────────────────────────────────


class TestGetAvailability:
    """GET /api/doctors/{doctorId}/availability"""

    @pytest.mark.asyncio
    async def test_get_availability_empty(self, client, token):
        fake_doctor_id = str(uuid.uuid4())
        resp = await client.get(
            f"{DOCTORS_BASE}/{fake_doctor_id}/availability",
            headers=_auth_headers(token),
        )
        assert resp.status_code == 200
        assert resp.json()["data"] == []

    @pytest.mark.asyncio
    async def test_get_availability_with_dow(self, client, token):
        fake_doctor_id = str(uuid.uuid4())
        resp = await client.get(
            f"{DOCTORS_BASE}/{fake_doctor_id}/availability?dow=1",
            headers=_auth_headers(token),
        )
        assert resp.status_code == 200
        assert isinstance(resp.json()["data"], list)


# ─────────────────────────────────────────────────────────────
# EXCEPTIONS
# ─────────────────────────────────────────────────────────────


class TestGetExceptions:
    """GET /api/doctors/{doctorId}/exceptions"""

    @pytest.mark.asyncio
    async def test_get_exceptions_empty(self, client, token):
        fake_doctor_id = str(uuid.uuid4())
        resp = await client.get(
            f"{DOCTORS_BASE}/{fake_doctor_id}/exceptions",
            headers=_auth_headers(token),
        )
        assert resp.status_code == 200
        assert resp.json()["data"] == []

    @pytest.mark.asyncio
    async def test_get_exceptions_with_date(self, client, token):
        fake_doctor_id = str(uuid.uuid4())
        resp = await client.get(
            f"{DOCTORS_BASE}/{fake_doctor_id}/exceptions?date=2026-01-15",
            headers=_auth_headers(token),
        )
        assert resp.status_code == 200
        assert isinstance(resp.json()["data"], list)


# ─────────────────────────────────────────────────────────────
# UNAUTHENTICATED
# ─────────────────────────────────────────────────────────────


class TestUnauthenticated:
    """Public GET endpoints return 200 without token; POST still requires auth."""

    @pytest.mark.asyncio
    async def test_specialties_without_token(self, client):
        resp = await client.get(SPECIALTIES_BASE)
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_doctors_without_token(self, client):
        resp = await client.get(DOCTORS_BASE)
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_create_specialty_without_token(self, client):
        resp = await client.post(
            SPECIALTIES_BASE, json={"name": "Unauthorized"}
        )
        assert resp.status_code in (401, 403)
