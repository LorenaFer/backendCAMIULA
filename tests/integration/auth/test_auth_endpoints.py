"""Tests de integración para endpoints de auth.

Usa la BD real (tesis_ula_local) con datos sembrados.
Los seeders deben haberse ejecutado antes de correr estos tests.

Cada test usa su propio AsyncClient para evitar contaminación
de estado entre tests por sesiones de BD compartidas.
"""

import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

BASE = "http://test"


def _client():
    return AsyncClient(transport=ASGITransport(app=app), base_url=BASE)


async def _login(email: str, password: str) -> str:
    async with _client() as c:
        resp = await c.post(
            "/api/auth/login",
            json={"email": email, "password": password},
        )
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Auth endpoints
# ---------------------------------------------------------------------------


class TestRegister:
    async def test_register_new_user(self):
        unique_email = f"pytest-{uuid.uuid4().hex[:8]}@test.com"
        async with _client() as c:
            resp = await c.post(
                "/api/auth/register",
                json={
                    "email": unique_email,
                    "full_name": "Pytest User",
                    "password": "pytest12345",
                },
            )
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "success"
        assert data["data"]["email"] == unique_email
        assert data["data"]["roles"] == ["paciente"]

    async def test_register_duplicate_email(self):
        async with _client() as c:
            resp = await c.post(
                "/api/auth/register",
                json={
                    "email": "admin@camiula.com",
                    "full_name": "Duplicate",
                    "password": "password123",
                },
            )
        assert resp.status_code == 409

    async def test_register_short_password(self):
        async with _client() as c:
            resp = await c.post(
                "/api/auth/register",
                json={
                    "email": "short@test.com",
                    "full_name": "Short",
                    "password": "123",
                },
            )
        assert resp.status_code == 422


class TestLogin:
    async def test_login_success(self):
        async with _client() as c:
            resp = await c.post(
                "/api/auth/login",
                json={"email": "admin@camiula.com", "password": "admin123"},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert "access_token" in data["data"]
        assert data["data"]["token_type"] == "bearer"

    async def test_login_wrong_password(self):
        async with _client() as c:
            resp = await c.post(
                "/api/auth/login",
                json={"email": "admin@camiula.com", "password": "wrongpass"},
            )
        assert resp.status_code == 401

    async def test_login_nonexistent_user(self):
        async with _client() as c:
            resp = await c.post(
                "/api/auth/login",
                json={"email": "nobody@test.com", "password": "password123"},
            )
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# RBAC
# ---------------------------------------------------------------------------


class TestRBAC:
    async def test_admin_can_list_users(self):
        token = await _login("admin@camiula.com", "admin123")
        async with _client() as c:
            resp = await c.get("/api/users", headers=_auth(token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert "items" in data["data"]
        assert "pagination" in data["data"]

    async def test_paciente_cannot_list_users(self):
        token = await _login("paciente@camiula.com", "paciente123")
        async with _client() as c:
            resp = await c.get("/api/users", headers=_auth(token))
        assert resp.status_code == 403
        assert "users:read" in resp.json()["message"]

    async def test_doctor_cannot_list_users(self):
        token = await _login("doctor@camiula.com", "doctor123")
        async with _client() as c:
            resp = await c.get("/api/users", headers=_auth(token))
        assert resp.status_code == 403

    async def test_all_roles_can_view_profile(self):
        for email, pwd in [
            ("admin@camiula.com", "admin123"),
            ("analista@camiula.com", "analista123"),
            ("doctor@camiula.com", "doctor123"),
            ("paciente@camiula.com", "paciente123"),
        ]:
            token = await _login(email, pwd)
            async with _client() as c:
                resp = await c.get("/api/users/me", headers=_auth(token))
            assert resp.status_code == 200, f"{email} should access /me"

    async def test_no_token_returns_403(self):
        async with _client() as c:
            resp = await c.get("/api/users/me")
        assert resp.status_code == 403


class TestRoleAssignment:
    async def test_admin_can_assign_role(self):
        async with _client() as c:
            # Login
            login_resp = await c.post(
                "/api/auth/login",
                json={"email": "admin@camiula.com", "password": "admin123"},
            )
            admin_token = login_resp.json()["data"]["access_token"]

            # List users to find paciente
            resp = await c.get("/api/users", headers=_auth(admin_token))
            users = resp.json()["data"]["items"]
            paciente = next(
                (u for u in users if u["email"] == "paciente@camiula.com"), None
            )
            assert paciente is not None

            # Assign role
            resp = await c.post(
                f"/api/users/{paciente['id']}/roles",
                json={"role_name": "analista"},
                headers=_auth(admin_token),
            )
            assert resp.status_code in (200, 409)

    async def test_paciente_cannot_assign_roles(self):
        async with _client() as c:
            login_resp = await c.post(
                "/api/auth/login",
                json={"email": "paciente@camiula.com", "password": "paciente123"},
            )
            token = login_resp.json()["data"]["access_token"]

            resp = await c.post(
                "/api/users/some-id/roles",
                json={"role_name": "administrador"},
                headers=_auth(token),
            )
            assert resp.status_code == 403
