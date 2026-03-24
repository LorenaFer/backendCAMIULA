from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.infrastructure.models import (
    PermissionModel,
    RoleModel,
    RolePermissionModel,
)
from app.shared.database.seeder import BaseSeeder

# Roles y sus permisos según la matriz
ROLE_PERMISSIONS = {
    "paciente": {
        "description": "Agendar y gestionar mis citas",
        "permissions": [
            "patients:read",
            "appointments:read",
            "appointments:create",
            "appointments:cancel",
            "doctors:read",
            "profile:read",
            "profile:update",
            "dashboard:view",
        ],
    },
    "analista": {
        "description": "Gestión de citas, pacientes y reportes",
        "permissions": [
            "patients:read",
            "patients:create",
            "patients:update",
            "appointments:read",
            "appointments:create",
            "appointments:update",
            "appointments:cancel",
            "doctors:read",
            "inventory:read",
            "inventory:update",
            "inventory:adjust",
            "reports:view",
            "reports:export",
            "profile:read",
            "profile:update",
            "dashboard:view",
        ],
    },
    "doctor": {
        "description": "Mis citas, disponibilidad y evaluaciones",
        "permissions": [
            "patients:read",
            "appointments:read",
            "appointments:cancel",
            "doctors:read",
            "doctors:availability",
            "reports:view",
            "profile:read",
            "profile:update",
            "dashboard:view",
        ],
    },
    "administrador": {
        "description": "Acceso completo al sistema",
        "permissions": [
            "patients:read",
            "patients:create",
            "patients:update",
            "patients:delete",
            "appointments:read",
            "appointments:create",
            "appointments:update",
            "appointments:cancel",
            "doctors:read",
            "doctors:availability",
            "inventory:read",
            "inventory:create",
            "inventory:update",
            "inventory:adjust",
            "users:read",
            "users:create",
            "users:update",
            "users:deactivate",
            "roles:read",
            "roles:assign",
            "reports:view",
            "reports:export",
            "profile:read",
            "profile:update",
            "dashboard:view",
        ],
    },
}


class RoleSeeder(BaseSeeder):
    """Siembra 4 roles + sus role_permissions. Idempotente."""

    order = 6

    async def run(self, session: AsyncSession) -> None:
        # Cargar mapa de permisos code → id
        result = await session.execute(select(PermissionModel))
        perm_map = {p.code: p.id for p in result.scalars()}

        for role_name, config in ROLE_PERMISSIONS.items():
            # Crear rol si no existe
            existing = await session.execute(
                select(RoleModel).where(RoleModel.name == role_name)
            )
            role = existing.scalar_one_or_none()
            if role is None:
                role = RoleModel(
                    id=str(uuid4()),
                    name=role_name,
                    description=config["description"],
                )
                session.add(role)
                await session.flush()

            # Asignar permisos
            for perm_code in config["permissions"]:
                perm_id = perm_map.get(perm_code)
                if perm_id is None:
                    continue

                exists = await session.execute(
                    select(RolePermissionModel).where(
                        RolePermissionModel.fk_role_id == role.id,
                        RolePermissionModel.fk_permission_id == perm_id,
                    )
                )
                if exists.scalar_one_or_none():
                    continue

                session.add(
                    RolePermissionModel(
                        id=str(uuid4()),
                        fk_role_id=role.id,
                        fk_permission_id=perm_id,
                    )
                )

    async def clear(self, session: AsyncSession) -> None:
        from sqlalchemy import delete

        role_names = list(ROLE_PERMISSIONS.keys())
        roles = await session.execute(
            select(RoleModel).where(RoleModel.name.in_(role_names))
        )
        role_ids = [r.id for r in roles.scalars()]

        if role_ids:
            await session.execute(
                delete(RolePermissionModel).where(
                    RolePermissionModel.fk_role_id.in_(role_ids)
                )
            )
        await session.execute(
            delete(RoleModel).where(RoleModel.name.in_(role_names))
        )
