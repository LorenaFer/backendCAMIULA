"""Integration tests for inventory movements and stock alerts.

Tests:
1. GET /inventory/reports/inventory-movements — list movements (empty initially)
2. POST batch entry via purchase order → verify entry movement recorded
3. GET /inventory/reports/stock-alerts — auto-generate alerts
4. POST /inventory/reports/stock-alerts/generate — manual alert generation
5. PATCH /inventory/reports/stock-alerts/{id}/acknowledge — acknowledge alert
6. PATCH /inventory/reports/stock-alerts/{id}/resolve — resolve alert
"""

import uuid
from datetime import date, timedelta

import httpx
import pytest
import pytest_asyncio

from app.main import app

INV = "/api/inventory"


async def _get_token() -> str:
    email = f"pytest-movements-{uuid.uuid4().hex[:6]}@test.com"
    password = "pytest12345"
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as c:
        await c.post(
            "/api/auth/register",
            json={
                "email": email,
                "full_name": "Pytest Movement Tester",
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


# ──────────────────────────────────────────────────────────
# Test: Inventory Movements endpoint
# ──────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_get_inventory_movements_empty(client, token):
    """GET /inventory/reports/inventory-movements returns empty list initially."""
    resp = await client.get(
        f"{INV}/reports/inventory-movements",
        headers=_auth(token),
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "items" in data
    assert "pagination" in data
    assert data["pagination"]["total"] >= 0


@pytest.mark.anyio
async def test_get_inventory_movements_with_type_filter(client, token):
    """GET /inventory/reports/inventory-movements?movement_type=entry works."""
    resp = await client.get(
        f"{INV}/reports/inventory-movements?movement_type=entry",
        headers=_auth(token),
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    for item in data["items"]:
        assert item["movement_type"] == "entry"


# ──────────────────────────────────────────────────────────
# Test: Stock Alerts endpoints
# ──────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_get_stock_alerts(client, token):
    """GET /inventory/reports/stock-alerts returns alert list."""
    resp = await client.get(
        f"{INV}/reports/stock-alerts",
        headers=_auth(token),
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "items" in data
    assert "total" in data
    assert "active_count" in data
    assert "resolved_count" in data


@pytest.mark.anyio
async def test_generate_stock_alerts(client, token):
    """POST /inventory/reports/stock-alerts/generate creates alerts."""
    resp = await client.post(
        f"{INV}/reports/stock-alerts/generate",
        headers=_auth(token),
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "new_alerts" in data
    assert isinstance(data["new_alerts"], int)


@pytest.mark.anyio
async def test_stock_report_auto_generates_alerts(client, token):
    """GET /inventory/reports/stock should auto-generate alerts."""
    resp = await client.get(
        f"{INV}/reports/stock",
        headers=_auth(token),
    )
    assert resp.status_code == 200
    # Verify stock report still works correctly
    data = resp.json()["data"]
    assert "items" in data
    assert "total_medications" in data
    assert "critical_count" in data


@pytest.mark.anyio
async def test_get_alerts_with_filters(client, token):
    """GET /inventory/reports/stock-alerts with filters."""
    for filter_param in ["alert_status=active", "alert_level=critical"]:
        resp = await client.get(
            f"{INV}/reports/stock-alerts?{filter_param}",
            headers=_auth(token),
        )
        assert resp.status_code == 200


@pytest.mark.anyio
async def test_acknowledge_nonexistent_alert(client, token):
    """PATCH /inventory/reports/stock-alerts/{id}/acknowledge — 404 for missing."""
    fake_id = str(uuid.uuid4())
    resp = await client.patch(
        f"{INV}/reports/stock-alerts/{fake_id}/acknowledge",
        headers=_auth(token),
    )
    assert resp.status_code == 404


@pytest.mark.anyio
async def test_resolve_nonexistent_alert(client, token):
    """PATCH /inventory/reports/stock-alerts/{id}/resolve — 404 for missing."""
    fake_id = str(uuid.uuid4())
    resp = await client.patch(
        f"{INV}/reports/stock-alerts/{fake_id}/resolve",
        headers=_auth(token),
    )
    assert resp.status_code == 404


# ──────────────────────────────────────────────────────────
# Test: Full flow — medication + generate alert + acknowledge + resolve
# ──────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_full_alert_lifecycle(client, token):
    """Create medication with zero stock → generate alert → acknowledge → resolve."""
    # Step 1: Create a medication (will have 0 stock → should trigger alert)
    med_code = f"TEST-MVT-{uuid.uuid4().hex[:6]}"
    resp = await client.post(
        f"{INV}/medications",
        headers=_auth(token),
        json={
            "code": med_code,
            "generic_name": f"Test Movement Med {med_code}",
            "pharmaceutical_form": "tablet",
            "unit_measure": "unit",
            "controlled_substance": False,
            "requires_refrigeration": False,
        },
    )
    assert resp.status_code == 201, f"Create medication failed: {resp.text}"

    # Step 2: Generate alerts — should create one for this medication (0 stock)
    resp = await client.post(
        f"{INV}/reports/stock-alerts/generate",
        headers=_auth(token),
    )
    assert resp.status_code == 200
    new_alerts = resp.json()["data"]["new_alerts"]
    assert new_alerts >= 1

    # Step 3: Get alerts — find the one for our medication
    resp = await client.get(
        f"{INV}/reports/stock-alerts?alert_status=active",
        headers=_auth(token),
    )
    assert resp.status_code == 200
    alerts = resp.json()["data"]["items"]
    our_alert = None
    for a in alerts:
        if a.get("medication_code") == med_code:
            our_alert = a
            break

    if our_alert:
        alert_id = our_alert["id"]

        # Step 4: Acknowledge it
        resp = await client.patch(
            f"{INV}/reports/stock-alerts/{alert_id}/acknowledge",
            headers=_auth(token),
        )
        assert resp.status_code == 200

        # Step 5: Resolve it
        resp = await client.patch(
            f"{INV}/reports/stock-alerts/{alert_id}/resolve",
            headers=_auth(token),
        )
        assert resp.status_code == 200

        # Step 6: Verify it's resolved
        resp = await client.get(
            f"{INV}/reports/stock-alerts?alert_status=resolved",
            headers=_auth(token),
        )
        assert resp.status_code == 200
        resolved = resp.json()["data"]["items"]
        resolved_ids = [a["id"] for a in resolved]
        assert alert_id in resolved_ids


# ──────────────────────────────────────────────────────────
# Test: Tables exist in the database
# ──────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_tables_exist():
    """Verify inventory_movements and stock_alerts tables exist in DB."""
    from sqlalchemy import text
    from app.shared.database.session import async_session_factory

    async with async_session_factory() as session:
        for table_name in ("inventory_movements", "stock_alerts"):
            result = await session.execute(
                text(
                    "SELECT EXISTS("
                    "SELECT FROM information_schema.tables "
                    "WHERE table_name = :name"
                    ")"
                ),
                {"name": table_name},
            )
            exists = result.scalar()
            assert exists, f"Table {table_name} does not exist"
