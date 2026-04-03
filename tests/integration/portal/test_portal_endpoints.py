"""Integration tests for the Patient Portal login endpoint.

Each test creates its own user / patient to avoid cross-test pollution.
"""

import uuid

import httpx
import pytest
import pytest_asyncio

from app.main import app

BASE_URL = "http://test"


def _client():
    return httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url=BASE_URL
    )


async def _get_token() -> str:
    """Register + login a fresh user and return a JWT token."""
    email = f"pytest-portal-{uuid.uuid4().hex[:8]}@test.com"
    password = "pytest12345"
    async with _client() as c:
        await c.post(
            "/api/auth/register",
            json={
                "email": email,
                "full_name": "Portal Tester",
                "password": password,
            },
        )
        resp = await c.post(
            "/api/auth/login",
            json={"email": email, "password": password},
        )
        assert resp.status_code == 200, f"Login failed: {resp.text}"
        return resp.json()["data"]["access_token"]


def _unique_cedula() -> str:
    return f"V-PORTAL-{uuid.uuid4().hex[:8]}"


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture
async def token():
    return await _get_token()


@pytest_asyncio.fixture
async def client():
    async with _client() as c:
        yield c


@pytest_asyncio.fixture
async def created_patient(client, token):
    """Create a patient and return its data dict."""
    cedula = _unique_cedula()
    resp = await client.post(
        "/api/patients",
        json={
            "cedula": cedula,
            "first_name": "Portal",
            "last_name": "TestPatient",
            "university_relation": "estudiante",
        },
        headers=_auth(token),
    )
    assert resp.status_code == 201, f"Patient creation failed: {resp.text}"
    return resp.json()["data"]


# ---------------------------------------------------------------------------
# Patient login tests
# ---------------------------------------------------------------------------


class TestPatientLoginByCedula:
    @pytest.mark.asyncio
    async def test_patient_found_by_cedula(self, client, created_patient):
        resp = await client.post(
            "/api/auth/patient/login",
            json={
                "query": created_patient["cedula"],
                "query_type": "cedula",
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "success"
        assert body["data"]["found"] is True
        patient = body["data"]["patient"]
        assert patient["id"] == created_patient["id"]
        assert patient["nhm"] == created_patient["nhm"]
        assert patient["first_name"] == "Portal"
        assert patient["last_name"] == "TestPatient"
        assert patient["university_relation"] == "estudiante"
        assert "is_new" in patient

    @pytest.mark.asyncio
    async def test_patient_not_found_by_cedula(self, client):
        resp = await client.post(
            "/api/auth/patient/login",
            json={
                "query": "V-NONEXISTENT-999",
                "query_type": "cedula",
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "success"
        assert body["data"]["found"] is False
        assert body["data"]["patient"] is None


class TestPatientLoginByNHM:
    @pytest.mark.asyncio
    async def test_patient_found_by_nhm(self, client, created_patient):
        resp = await client.post(
            "/api/auth/patient/login",
            json={
                "query": str(created_patient["nhm"]),
                "query_type": "nhm",
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["data"]["found"] is True
        assert body["data"]["patient"]["id"] == created_patient["id"]

    @pytest.mark.asyncio
    async def test_patient_not_found_by_nhm(self, client):
        resp = await client.post(
            "/api/auth/patient/login",
            json={
                "query": "999999",
                "query_type": "nhm",
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["data"]["found"] is False
        assert body["data"]["patient"] is None


class TestPatientLoginValidation:
    @pytest.mark.asyncio
    async def test_invalid_query_type(self, client):
        resp = await client.post(
            "/api/auth/patient/login",
            json={
                "query": "V-12345678",
                "query_type": "email",
            },
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_empty_query(self, client):
        resp = await client.post(
            "/api/auth/patient/login",
            json={
                "query": "",
                "query_type": "cedula",
            },
        )
        assert resp.status_code == 422


class TestPatientLoginNoAuthRequired:
    @pytest.mark.asyncio
    async def test_no_token_needed(self):
        """Patient login should work without any auth header."""
        async with _client() as c:
            resp = await c.post(
                "/api/auth/patient/login",
                json={
                    "query": "V-NO-AUTH-TEST",
                    "query_type": "cedula",
                },
            )
        assert resp.status_code == 200
        body = resp.json()
        assert body["data"]["found"] is False


# ---------------------------------------------------------------------------
# Full flow: register patient -> login via portal
# ---------------------------------------------------------------------------


class TestFullPortalFlow:
    @pytest.mark.asyncio
    async def test_register_then_portal_login(self):
        """Register a patient via staff endpoint, then login via portal."""
        token = await _get_token()
        cedula = _unique_cedula()

        async with _client() as c:
            # 1. Staff registers the patient
            reg_resp = await c.post(
                "/api/patients",
                json={
                    "cedula": cedula,
                    "first_name": "FlowTest",
                    "last_name": "Patient",
                    "university_relation": "profesor",
                },
                headers=_auth(token),
            )
            assert reg_resp.status_code == 201
            patient_data = reg_resp.json()["data"]

            # 2. Patient logs in via portal (no password)
            login_resp = await c.post(
                "/api/auth/patient/login",
                json={"query": cedula, "query_type": "cedula"},
            )
            assert login_resp.status_code == 200
            login_body = login_resp.json()
            assert login_body["data"]["found"] is True
            assert login_body["data"]["patient"]["id"] == patient_data["id"]
            assert login_body["data"]["patient"]["nhm"] == patient_data["nhm"]

            # 3. Also login by NHM
            nhm_resp = await c.post(
                "/api/auth/patient/login",
                json={
                    "query": str(patient_data["nhm"]),
                    "query_type": "nhm",
                },
            )
            assert nhm_resp.status_code == 200
            assert nhm_resp.json()["data"]["found"] is True
