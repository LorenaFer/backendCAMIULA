"""Integration tests for Patient endpoints.

Each test exercises the full HTTP endpoint (router -> use case -> repo -> DB).
Uses httpx.AsyncClient against the real FastAPI app with the test DB.
"""

import uuid

import httpx
import pytest
import pytest_asyncio

from app.main import app

BASE = "/api/patients"


def _unique_cedula() -> str:
    return f"V-TEST-{uuid.uuid4().hex[:8]}"


async def _get_token() -> str:
    """Gets a valid JWT token for authenticated requests."""
    email = f"pytest-patients-{uuid.uuid4().hex[:6]}@test.com"
    password = "pytest12345"
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as c:
        # Register a fresh user
        await c.post(
            "/api/auth/register",
            json={
                "email": email,
                "full_name": "Pytest Patient Tester",
                "password": password,
            },
        )
        # Login to get token
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


class TestCreatePatient:
    """POST /api/patients"""

    @pytest.mark.asyncio
    async def test_create_patient_success(self, client, token):
        cedula = _unique_cedula()
        resp = await client.post(
            BASE,
            json={
                "cedula": cedula,
                "first_name": "Juan",
                "last_name": "Perez",
                "university_relation": "estudiante",
            },
            headers=_auth_headers(token),
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["status"] == "success"
        assert body["data"]["cedula"] == cedula
        assert body["data"]["nhm"] >= 1
        assert body["data"]["is_new"] is True

    @pytest.mark.asyncio
    async def test_create_patient_duplicate_cedula(self, client, token):
        cedula = _unique_cedula()
        await client.post(
            BASE,
            json={
                "cedula": cedula,
                "first_name": "Ana",
                "last_name": "Lopez",
                "university_relation": "empleado",
            },
            headers=_auth_headers(token),
        )
        resp = await client.post(
            BASE,
            json={
                "cedula": cedula,
                "first_name": "Maria",
                "last_name": "Garcia",
                "university_relation": "profesor",
            },
            headers=_auth_headers(token),
        )
        assert resp.status_code == 409
        assert "ya existe" in resp.json()["message"].lower()

    @pytest.mark.asyncio
    async def test_create_patient_missing_fields(self, client, token):
        resp = await client.post(
            BASE,
            json={"cedula": _unique_cedula()},
            headers=_auth_headers(token),
        )
        assert resp.status_code == 422


class TestSearchPatient:
    """GET /api/patients?nhm=X / ?cedula=X"""

    @pytest.mark.asyncio
    async def test_search_by_cedula(self, client, token):
        cedula = _unique_cedula()
        create_resp = await client.post(
            BASE,
            json={
                "cedula": cedula,
                "first_name": "Carlos",
                "last_name": "Mendoza",
                "university_relation": "estudiante",
            },
            headers=_auth_headers(token),
        )
        assert create_resp.status_code == 201

        resp = await client.get(
            f"{BASE}?cedula={cedula}", headers=_auth_headers(token)
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data is not None
        assert data["first_name"] == "Carlos"
        # PatientPublic should NOT have sensitive fields
        assert "home_address" not in data
        assert "medical_data" not in data

    @pytest.mark.asyncio
    async def test_search_by_nhm(self, client, token):
        cedula = _unique_cedula()
        create_resp = await client.post(
            BASE,
            json={
                "cedula": cedula,
                "first_name": "Pedro",
                "last_name": "Ramirez",
                "university_relation": "empleado",
            },
            headers=_auth_headers(token),
        )
        nhm = create_resp.json()["data"]["nhm"]

        resp = await client.get(
            f"{BASE}?nhm={nhm}", headers=_auth_headers(token)
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["nhm"] == nhm

    @pytest.mark.asyncio
    async def test_search_not_found(self, client, token):
        resp = await client.get(
            f"{BASE}?cedula=V-NO-EXISTE-999", headers=_auth_headers(token)
        )
        assert resp.status_code == 200
        assert resp.json()["data"] is None


class TestGetPatientFull:
    """GET /api/patients/full"""

    @pytest.mark.asyncio
    async def test_full_by_cedula(self, client, token):
        cedula = _unique_cedula()
        await client.post(
            BASE,
            json={
                "cedula": cedula,
                "first_name": "Luis",
                "last_name": "Torres",
                "university_relation": "profesor",
                "phone": "0412-1234567",
                "medical_data": {"blood_type": "O+"},
            },
            headers=_auth_headers(token),
        )

        resp = await client.get(
            f"{BASE}/full?cedula={cedula}", headers=_auth_headers(token)
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["cedula"] == cedula
        assert data["phone"] == "0412-1234567"
        assert data["medical_data"]["blood_type"] == "O+"

    @pytest.mark.asyncio
    async def test_full_not_found(self, client, token):
        resp = await client.get(
            f"{BASE}/full?nhm=999999", headers=_auth_headers(token)
        )
        assert resp.status_code == 200
        assert resp.json()["data"] is None


class TestListPatients:
    """GET /api/patients — paginated list."""

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
        assert body["data"]["pagination"]["page_size"] == 5


class TestMaxNhm:
    """GET /api/patients/max-nhm"""

    @pytest.mark.asyncio
    async def test_max_nhm(self, client, token):
        resp = await client.get(
            f"{BASE}/max-nhm", headers=_auth_headers(token)
        )
        assert resp.status_code == 200
        assert "max_nhm" in resp.json()["data"]
        assert isinstance(resp.json()["data"]["max_nhm"], int)


class TestRegisterPatient:
    """POST /api/patients/register"""

    @pytest.mark.asyncio
    async def test_register_basic(self, client, token):
        cedula = _unique_cedula()
        resp = await client.post(
            f"{BASE}/register",
            json={
                "cedula": cedula,
                "first_name": "Maria",
                "last_name": "Fernandez",
                "university_relation": "estudiante",
                "phone": "0414-9876543",
                "sex": "F",
                "birth_date": "2000-05-15",
                "country": "Venezuela",
                "state_geo": "Merida",
                "city": "Merida",
                "blood_type": "A+",
                "allergies": "Penicilina, Polvo",
                "emergency_name": "Jose Fernandez",
                "emergency_phone": "0412-1112233",
            },
            headers=_auth_headers(token),
        )
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["is_new"] is True
        assert data["nhm"] >= 1

    @pytest.mark.asyncio
    async def test_register_duplicate_cedula(self, client, token):
        cedula = _unique_cedula()
        await client.post(
            f"{BASE}/register",
            json={
                "cedula": cedula,
                "first_name": "Test",
                "last_name": "Dup",
                "university_relation": "empleado",
            },
            headers=_auth_headers(token),
        )
        resp = await client.post(
            f"{BASE}/register",
            json={
                "cedula": cedula,
                "first_name": "Test2",
                "last_name": "Dup2",
                "university_relation": "empleado",
            },
            headers=_auth_headers(token),
        )
        assert resp.status_code == 409


class TestUnauthenticated:
    """Endpoints without token must return 401/403."""

    @pytest.mark.asyncio
    async def test_list_without_token(self, client):
        resp = await client.get(BASE)
        assert resp.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_create_without_token(self, client):
        resp = await client.post(
            BASE,
            json={
                "cedula": "V-0",
                "first_name": "X",
                "last_name": "Y",
                "university_relation": "estudiante",
            },
        )
        assert resp.status_code in (401, 403)
