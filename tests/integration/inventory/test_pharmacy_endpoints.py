"""Integration tests for Pharmacy endpoints (prescriptions, suppliers, batches, limits, exceptions).

Each test exercises the full HTTP endpoint (router -> repo -> DB).
Uses httpx.AsyncClient against the real FastAPI app with the test DB.
"""

import uuid
from datetime import date, timedelta

import httpx
import pytest
import pytest_asyncio

from app.main import app

INV = "/api/inventory"


async def _get_token() -> str:
    """Register a fresh user and return a valid JWT token."""
    email = f"pytest-pharmacy-{uuid.uuid4().hex[:6]}@test.com"
    password = "pytest12345"
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as c:
        await c.post(
            "/api/auth/register",
            json={
                "email": email,
                "full_name": "Pytest Pharmacy Tester",
                "password": password,
            },
        )
        resp = await c.post(
            "/api/auth/login", json={"email": email, "password": password}
        )
        assert resp.status_code == 200, f"Login failed: {resp.text}"
        return resp.json()["data"]["access_token"]


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
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c


# ==================================================================
# Helper: create a medication (needed for prescriptions, batches, limits)
# ==================================================================

async def _create_medication(client: httpx.AsyncClient, token: str) -> str:
    """Create a medication and return its ID."""
    code = f"MED-TEST-{uuid.uuid4().hex[:8]}"
    resp = await client.post(
        f"{INV}/medications",
        json={
            "code": code,
            "generic_name": f"TestMed {code}",
            "pharmaceutical_form": "Tablets",
            "unit_measure": "Tablets",
            "controlled_substance": False,
            "requires_refrigeration": False,
        },
        headers=_auth(token),
    )
    assert resp.status_code == 201, f"Medication creation failed: {resp.text}"
    return resp.json()["data"]["id"]


# ==================================================================
# SUPPLIERS
# ==================================================================


class TestSuppliers:

    @pytest.mark.asyncio
    async def test_create_supplier(self, client, token):
        rif = f"J-{uuid.uuid4().hex[:8]}"
        resp = await client.post(
            f"{INV}/suppliers",
            json={"name": "Test Supplier", "rif": rif},
            headers=_auth(token),
        )
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["rif"] == rif
        assert data["supplier_status"] == "active"

    @pytest.mark.asyncio
    async def test_create_duplicate_rif(self, client, token):
        rif = f"J-{uuid.uuid4().hex[:8]}"
        await client.post(
            f"{INV}/suppliers",
            json={"name": "First", "rif": rif},
            headers=_auth(token),
        )
        resp = await client.post(
            f"{INV}/suppliers",
            json={"name": "Second", "rif": rif},
            headers=_auth(token),
        )
        assert resp.status_code == 409

    @pytest.mark.asyncio
    async def test_list_suppliers(self, client, token):
        resp = await client.get(
            f"{INV}/suppliers?page=1&page_size=5",
            headers=_auth(token),
        )
        assert resp.status_code == 200
        body = resp.json()["data"]
        assert "items" in body
        assert "pagination" in body

    @pytest.mark.asyncio
    async def test_get_supplier_by_id(self, client, token):
        rif = f"J-{uuid.uuid4().hex[:8]}"
        create = await client.post(
            f"{INV}/suppliers",
            json={"name": "GetMe", "rif": rif},
            headers=_auth(token),
        )
        sid = create.json()["data"]["id"]
        resp = await client.get(f"{INV}/suppliers/{sid}", headers=_auth(token))
        assert resp.status_code == 200
        assert resp.json()["data"]["name"] == "GetMe"

    @pytest.mark.asyncio
    async def test_get_supplier_not_found(self, client, token):
        resp = await client.get(
            f"{INV}/suppliers/nonexistent-id", headers=_auth(token)
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_update_supplier(self, client, token):
        rif = f"J-{uuid.uuid4().hex[:8]}"
        create = await client.post(
            f"{INV}/suppliers",
            json={"name": "Before", "rif": rif},
            headers=_auth(token),
        )
        sid = create.json()["data"]["id"]
        resp = await client.patch(
            f"{INV}/suppliers/{sid}",
            json={"name": "After"},
            headers=_auth(token),
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["name"] == "After"

    @pytest.mark.asyncio
    async def test_supplier_options(self, client, token):
        resp = await client.get(
            f"{INV}/suppliers/options", headers=_auth(token)
        )
        assert resp.status_code == 200


# ==================================================================
# PRESCRIPTIONS
# ==================================================================


class TestPrescriptions:

    @pytest.mark.asyncio
    async def test_create_prescription(self, client, token):
        med_id = await _create_medication(client, token)
        resp = await client.post(
            f"{INV}/prescriptions",
            json={
                "fk_appointment_id": str(uuid.uuid4()),
                "fk_patient_id": str(uuid.uuid4()),
                "fk_doctor_id": str(uuid.uuid4()),
                "items": [
                    {
                        "medication_id": med_id,
                        "quantity_prescribed": 10,
                        "dosage_instructions": "1 every 8h",
                    }
                ],
            },
            headers=_auth(token),
        )
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["prescription_status"] == "issued"
        assert len(data["items"]) == 1

    @pytest.mark.asyncio
    async def test_get_prescription_by_id(self, client, token):
        med_id = await _create_medication(client, token)
        create = await client.post(
            f"{INV}/prescriptions",
            json={
                "fk_appointment_id": str(uuid.uuid4()),
                "fk_patient_id": str(uuid.uuid4()),
                "fk_doctor_id": str(uuid.uuid4()),
                "items": [
                    {"medication_id": med_id, "quantity_prescribed": 5}
                ],
            },
            headers=_auth(token),
        )
        pid = create.json()["data"]["id"]
        resp = await client.get(
            f"{INV}/prescriptions/{pid}", headers=_auth(token)
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["id"] == pid

    @pytest.mark.asyncio
    async def test_get_prescription_not_found(self, client, token):
        resp = await client.get(
            f"{INV}/prescriptions/nonexistent-id", headers=_auth(token)
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_search_by_appointment(self, client, token):
        med_id = await _create_medication(client, token)
        appt_id = str(uuid.uuid4())
        await client.post(
            f"{INV}/prescriptions",
            json={
                "fk_appointment_id": appt_id,
                "fk_patient_id": str(uuid.uuid4()),
                "fk_doctor_id": str(uuid.uuid4()),
                "items": [
                    {"medication_id": med_id, "quantity_prescribed": 3}
                ],
            },
            headers=_auth(token),
        )
        resp = await client.get(
            f"{INV}/prescriptions?appointment_id={appt_id}",
            headers=_auth(token),
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["fk_appointment_id"] == appt_id

    @pytest.mark.asyncio
    async def test_search_by_patient(self, client, token):
        med_id = await _create_medication(client, token)
        patient_id = str(uuid.uuid4())
        await client.post(
            f"{INV}/prescriptions",
            json={
                "fk_appointment_id": str(uuid.uuid4()),
                "fk_patient_id": patient_id,
                "fk_doctor_id": str(uuid.uuid4()),
                "items": [
                    {"medication_id": med_id, "quantity_prescribed": 2}
                ],
            },
            headers=_auth(token),
        )
        resp = await client.get(
            f"{INV}/prescriptions?patient_id={patient_id}",
            headers=_auth(token),
        )
        assert resp.status_code == 200
        body = resp.json()["data"]
        assert "items" in body
        assert body["pagination"]["total"] >= 1

    @pytest.mark.asyncio
    async def test_search_no_filter(self, client, token):
        resp = await client.get(
            f"{INV}/prescriptions", headers=_auth(token)
        )
        assert resp.status_code == 200
        assert resp.json()["data"] == []


# ==================================================================
# BATCHES
# ==================================================================


class TestBatches:

    @pytest.mark.asyncio
    async def test_list_batches(self, client, token):
        resp = await client.get(
            f"{INV}/batches?page=1&page_size=5",
            headers=_auth(token),
        )
        assert resp.status_code == 200
        body = resp.json()["data"]
        assert "items" in body
        assert "pagination" in body

    @pytest.mark.asyncio
    async def test_get_batch_not_found(self, client, token):
        resp = await client.get(
            f"{INV}/batches/nonexistent-id", headers=_auth(token)
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_list_batches_with_filters(self, client, token):
        future_date = (date.today() + timedelta(days=365)).isoformat()
        resp = await client.get(
            f"{INV}/batches?status=available&expiring_before={future_date}&page=1&page_size=10",
            headers=_auth(token),
        )
        assert resp.status_code == 200


# ==================================================================
# DISPATCH LIMITS
# ==================================================================


class TestDispatchLimits:

    @pytest.mark.asyncio
    async def test_create_limit(self, client, token):
        med_id = await _create_medication(client, token)
        resp = await client.post(
            f"{INV}/dispatch-limits",
            json={
                "fk_medication_id": med_id,
                "monthly_max_quantity": 30,
                "applies_to": "all",
            },
            headers=_auth(token),
        )
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["monthly_max_quantity"] == 30
        assert data["active"] is True

    @pytest.mark.asyncio
    async def test_list_limits(self, client, token):
        resp = await client.get(
            f"{INV}/dispatch-limits?page=1&page_size=5",
            headers=_auth(token),
        )
        assert resp.status_code == 200
        body = resp.json()["data"]
        assert "items" in body

    @pytest.mark.asyncio
    async def test_update_limit(self, client, token):
        med_id = await _create_medication(client, token)
        create = await client.post(
            f"{INV}/dispatch-limits",
            json={
                "fk_medication_id": med_id,
                "monthly_max_quantity": 20,
            },
            headers=_auth(token),
        )
        lid = create.json()["data"]["id"]
        resp = await client.patch(
            f"{INV}/dispatch-limits/{lid}",
            json={"monthly_max_quantity": 50},
            headers=_auth(token),
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["monthly_max_quantity"] == 50

    @pytest.mark.asyncio
    async def test_update_limit_not_found(self, client, token):
        resp = await client.patch(
            f"{INV}/dispatch-limits/nonexistent-id",
            json={"monthly_max_quantity": 10},
            headers=_auth(token),
        )
        assert resp.status_code == 404


# ==================================================================
# DISPATCH EXCEPTIONS
# ==================================================================


class TestDispatchExceptions:

    @pytest.mark.asyncio
    async def test_create_exception(self, client, token):
        med_id = await _create_medication(client, token)
        resp = await client.post(
            f"{INV}/dispatch-exceptions",
            json={
                "fk_patient_id": str(uuid.uuid4()),
                "fk_medication_id": med_id,
                "authorized_quantity": 60,
                "valid_from": date.today().isoformat(),
                "valid_until": (date.today() + timedelta(days=90)).isoformat(),
                "reason": "Chronic condition requires higher dosage",
            },
            headers=_auth(token),
        )
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["authorized_quantity"] == 60

    @pytest.mark.asyncio
    async def test_list_exceptions(self, client, token):
        resp = await client.get(
            f"{INV}/dispatch-exceptions?page=1&page_size=5",
            headers=_auth(token),
        )
        assert resp.status_code == 200
        body = resp.json()["data"]
        assert "items" in body

    @pytest.mark.asyncio
    async def test_list_exceptions_filter_by_patient(self, client, token):
        patient_id = str(uuid.uuid4())
        resp = await client.get(
            f"{INV}/dispatch-exceptions?patient_id={patient_id}",
            headers=_auth(token),
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["pagination"]["total"] == 0


# ==================================================================
# AUTH — Unauthenticated requests must be rejected
# ==================================================================


class TestUnauthenticated:

    @pytest.mark.asyncio
    async def test_suppliers_without_token(self, client):
        resp = await client.get(f"{INV}/suppliers")
        assert resp.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_prescriptions_without_token(self, client):
        resp = await client.get(f"{INV}/prescriptions")
        assert resp.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_batches_without_token(self, client):
        resp = await client.get(f"{INV}/batches")
        assert resp.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_limits_without_token(self, client):
        resp = await client.get(f"{INV}/dispatch-limits")
        assert resp.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_exceptions_without_token(self, client):
        resp = await client.get(f"{INV}/dispatch-exceptions")
        assert resp.status_code in (401, 403)
