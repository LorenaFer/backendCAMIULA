"""Utilidades compartidas de la capa de presentación del módulo auth."""

from __future__ import annotations

from app.modules.auth.domain.entities.user import User
from app.modules.auth.presentation.schemas.auth_schema import MeResponse

# Mapeo de nombres de rol interno → nombre para el frontend
_ROLE_DISPLAY = {"administrador": "admin"}


def build_me_response(user: User) -> dict:
    """Construye el dict de MeResponse a partir de un User entity.

    Usado tanto en /auth/login como en /users/me para garantizar
    consistencia en el formato de respuesta del usuario autenticado.
    """
    parts = user.full_name.strip().split()
    initials = "".join(p[0].upper() for p in parts[:2]) if parts else "??"
    role = user.roles[0] if user.roles else "paciente"
    role = _ROLE_DISPLAY.get(role, role)
    return MeResponse(
        id=user.id,
        name=user.full_name,
        role=role,
        initials=initials,
        doctor_id=user.doctor_id,
    ).model_dump()
