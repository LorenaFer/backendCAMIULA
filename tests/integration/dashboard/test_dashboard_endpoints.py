"""Integration tests for Dashboard BI endpoints.

Tests all 5 dashboard-related endpoints return 200 with the expected shape.
Uses function-scoped fixtures with a fresh user per test.
"""

import uuid

import httpx
import pytest
import pytest_asyncio

from app.main import app


async def _get_token() -> str:
    """Register + login a fresh user, return JWT."""
    email = f"pytest-dash-{uuid.uuid4().hex[:6]}@test.com"
    password = "pytest12345"
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as c:
        await c.post(
            "/api/auth/register",
            json={
                "email": email,
                "full_name": "Pytest Dashboard Tester",
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


@pytest_asyncio.fixture
async def token():
    return await _get_token()


@pytest_asyncio.fixture
async def client():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c


# ------------------------------------------------------------------
# 1. GET /api/dashboard
# ------------------------------------------------------------------


class TestDashboard:
    @pytest.mark.asyncio
    async def test_dashboard_returns_200(self, client, token):
        resp = await client.get(
            "/api/dashboard?periodo=month", headers=_auth(token)
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["status"] == "success"
        data = body["data"]

        # Verify top-level keys
        assert "fecha" in data
        assert "generated_at" in data
        assert "kpis" in data
        assert "appointments_by_status" in data
        assert "appointments_by_specialty" in data
        assert "daily_trend" in data
        assert isinstance(data["daily_trend"], list)
        assert "hourly_distribution" in data
        assert "heatmap" in data
        assert isinstance(data["heatmap"], list)
        assert "occupancy_by_specialty" in data
        assert "absenteeism_by_specialty" in data
        assert "performance_by_doctor" in data
        assert "patients_by_type" in data
        assert "patients_by_sex" in data
        assert "first_time_count" in data
        assert "returning_count" in data
        assert "top_diagnoses" in data
        assert "inventory" in data
        assert "top_consumption" in data

        # KPIs shape
        kpis = data["kpis"]
        for key in [
            "total_appointments",
            "appointments_today",
            "pending_appointments",
            "attendance_rate",
            "no_show_rate",
            "cancellation_rate",
            "total_patients",
            "new_patients",
            "total_doctors",
            "inventory_value",
        ]:
            assert key in kpis

        # Heatmap: 5 rows x 12 cols
        assert len(data["heatmap"]) == 5
        for row in data["heatmap"]:
            assert len(row) == 12

    @pytest.mark.asyncio
    async def test_dashboard_with_explicit_date(self, client, token):
        resp = await client.get(
            "/api/dashboard?fecha=2026-01-15&periodo=week",
            headers=_auth(token),
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["fecha"] == "2026-01-15"


# ------------------------------------------------------------------
# 2. GET /api/medical-records/diagnostics/top
# ------------------------------------------------------------------


class TestTopDiagnostics:
    @pytest.mark.asyncio
    async def test_top_diagnostics_returns_200(self, client, token):
        resp = await client.get(
            "/api/medical-records/diagnostics/top?limit=3",
            headers=_auth(token),
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["status"] == "success"
        assert isinstance(body["data"], list)

    @pytest.mark.asyncio
    async def test_top_diagnostics_with_periodo(self, client, token):
        resp = await client.get(
            "/api/medical-records/diagnostics/top?limit=5&periodo=year",
            headers=_auth(token),
        )
        assert resp.status_code == 200


# ------------------------------------------------------------------
# 3. GET /api/doctors/availability/summary
# ------------------------------------------------------------------


class TestAvailabilitySummary:
    @pytest.mark.asyncio
    async def test_availability_summary_returns_200(self, client, token):
        resp = await client.get(
            "/api/doctors/availability/summary",
            headers=_auth(token),
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["status"] == "success"
        assert isinstance(body["data"], list)


# ------------------------------------------------------------------
# 4. GET /api/appointments/heatmap
# ------------------------------------------------------------------


class TestAppointmentsHeatmap:
    @pytest.mark.asyncio
    async def test_heatmap_returns_200(self, client, token):
        resp = await client.get(
            "/api/appointments/heatmap?fecha_desde=2026-01-01&fecha_hasta=2026-12-31",
            headers=_auth(token),
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["status"] == "success"
        data = body["data"]
        assert "heatmap" in data
        assert "fecha_desde" in data
        assert "fecha_hasta" in data
        assert len(data["heatmap"]) == 5
        for row in data["heatmap"]:
            assert len(row) == 12


# ------------------------------------------------------------------
# 5. GET /api/patients/demographics
# ------------------------------------------------------------------


class TestPatientDemographics:
    @pytest.mark.asyncio
    async def test_demographics_returns_200(self, client, token):
        resp = await client.get(
            "/api/patients/demographics",
            headers=_auth(token),
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["status"] == "success"
        data = body["data"]
        assert "patients_by_type" in data
        assert "patients_by_sex" in data
        assert "first_time_count" in data
        assert "returning_count" in data
