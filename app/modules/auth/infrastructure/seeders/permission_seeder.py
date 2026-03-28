from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.infrastructure.models import PermissionModel
from app.shared.database.seeder import BaseSeeder

# Matriz completa de permisos del sistema
PERMISSIONS = [
    ("patients:read", "patients", "Ver pacientes"),
    ("patients:create", "patients", "Crear pacientes"),
    ("patients:update", "patients", "Actualizar pacientes"),
    ("patients:delete", "patients", "Eliminar pacientes"),
    ("appointments:read", "appointments", "Ver citas"),
    ("appointments:create", "appointments", "Crear citas"),
    ("appointments:update", "appointments", "Actualizar citas"),
    ("appointments:cancel", "appointments", "Cancelar citas"),
    ("doctors:read", "appointments", "Ver doctores"),
    ("doctors:availability", "appointments", "Gestionar disponibilidad"),
    ("inventory:read", "inventory", "Ver inventario"),
    ("inventory:create", "inventory", "Crear items de inventario"),
    ("inventory:update", "inventory", "Actualizar inventario"),
    ("inventory:adjust", "inventory", "Ajustar cantidades de inventario"),
    ("users:read", "auth", "Ver usuarios"),
    ("users:create", "auth", "Crear usuarios"),
    ("users:update", "auth", "Actualizar usuarios"),
    ("users:deactivate", "auth", "Desactivar usuarios"),
    ("roles:read", "auth", "Ver roles"),
    ("roles:assign", "auth", "Asignar roles"),
    ("reports:view", "reports", "Ver reportes"),
    ("reports:export", "reports", "Exportar reportes"),
    ("profile:read", "auth", "Ver perfil propio"),
    ("profile:update", "auth", "Actualizar perfil propio"),
    ("dashboard:view", "auth", "Ver dashboard"),
    # Medical records (appointments module)
    ("medical_records:read", "appointments", "Ver expedientes médicos"),
    ("medical_records:write", "appointments", "Editar evaluaciones médicas"),
    ("medical_records:prepare", "appointments", "Preparar expediente (enfermería)"),
    # Availability (appointments module)
    ("availability:read", "appointments", "Ver disponibilidad de doctores"),
    ("availability:manage", "appointments", "Gestionar bloques de disponibilidad"),
]


class PermissionSeeder(BaseSeeder):
    """Siembra los 25 permisos del sistema. Idempotente por code."""

    order = 5

    async def run(self, session: AsyncSession) -> None:
        for code, module, description in PERMISSIONS:
            existing = await session.execute(
                select(PermissionModel).where(PermissionModel.code == code)
            )
            if existing.scalar_one_or_none():
                continue
            session.add(
                PermissionModel(
                    id=str(uuid4()),
                    code=code,
                    module=module,
                    description=description,
                )
            )

    async def clear(self, session: AsyncSession) -> None:
        from sqlalchemy import delete

        codes = [code for code, _, _ in PERMISSIONS]
        await session.execute(
            delete(PermissionModel).where(PermissionModel.code.in_(codes))
        )
