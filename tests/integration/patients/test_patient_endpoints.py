"""Tests de integración para endpoints de pacientes."""

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


@pytest.mark.asyncio
async def test_create_and_search_patient_success():
    token = await _login("admin@camiula.com", "admin123")
    cedula = f"V-{uuid.uuid4().hex[:8]}"

    payload = {
        "cedula": cedula,
        "nombre": "Pedro",
        "apellido": "Gonzalez",
        "sexo": "M",
        "estado_civil": "casado",
        "relacion_univ": "E",
        "datos_medicos": {
            "tipo_sangre": "O+",
            "alergias": ["Penicilina"],
            "numero_contacto": "04121234567",
            "condiciones": ["Hipertension"],
        },
    }

    async with _client() as c:
        created = await c.post(
            "/api/patients",
            json=payload,
            headers=_auth(token),
        )

    assert created.status_code == 201, created.text
    created_data = created.json()["data"]
    assert created_data["cedula"] == cedula
    assert created_data["relacion_univ"] == "empleado"

    nhm = created_data["nhm"]

    async with _client() as c:
        by_cedula = await c.get(
            f"/api/patients/search?cedula={cedula}", headers=_auth(token)
        )
        by_nhm = await c.get(f"/api/patients/search?nhm={nhm}", headers=_auth(token))

    assert by_cedula.status_code == 200
    assert by_cedula.json()["data"]["id"] == created_data["id"]
    assert by_nhm.status_code == 200
    assert by_nhm.json()["data"]["cedula"] == cedula


@pytest.mark.asyncio
async def test_search_requires_exactly_one_parameter():
    token = await _login("admin@camiula.com", "admin123")

    async with _client() as c:
        both = await c.get(
            "/api/patients/search?cedula=V-12345678&nhm=100245",
            headers=_auth(token),
        )
        none = await c.get("/api/patients/search", headers=_auth(token))

    assert both.status_code == 400
    assert both.json()["message"] == "Debe enviar cedula o nhm, pero no ambos"
    assert none.status_code == 400
    assert none.json()["message"] == "Debe enviar cedula o nhm, pero no ambos"


@pytest.mark.asyncio
async def test_get_history_returns_404_for_unknown_patient():
    token = await _login("admin@camiula.com", "admin123")
    unknown_id = str(uuid.uuid4())

    async with _client() as c:
        response = await c.get(
            f"/api/patients/{unknown_id}/history",
            headers=_auth(token),
        )

    assert response.status_code == 404
    assert response.json()["message"] == "Paciente no encontrado"
