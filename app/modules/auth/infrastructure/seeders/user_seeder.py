from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.modules.auth.domain.entities.enums import UserStatus
from app.modules.auth.infrastructure.models import (
    RoleModel,
    UserModel,
    UserRoleModel,
)
from app.shared.database.seeder import BaseSeeder

# Usuarios de prueba — uno por rol
TEST_USERS = [
    {
        "email": "admin@camiula.com",
        "full_name": "Administrador CAMIULA",
        "password": "admin123",
        "role": "administrador",
    },
    {
        "email": "analista@camiula.com",
        "full_name": "Ana Lista",
        "password": "analista123",
        "role": "analista",
    },
    {
        "email": "doctor@camiula.com",
        "full_name": "Dr. Carlos Médico",
        "password": "doctor123",
        "role": "doctor",
    },
    {
        "email": "paciente@camiula.com",
        "full_name": "Pedro Paciente",
        "password": "paciente123",
        "role": "paciente",
    },
]


class UserSeeder(BaseSeeder):
    """Siembra usuarios de prueba con sus roles asignados."""

    order = 10

    async def run(self, session: AsyncSession) -> None:
        for user_data in TEST_USERS:
            existing = await session.execute(
                select(UserModel).where(
                    UserModel.email == user_data["email"]
                )
            )
            if existing.scalar_one_or_none():
                continue

            user = UserModel(
                id=str(uuid4()),
                email=user_data["email"],
                full_name=user_data["full_name"],
                hashed_password=hash_password(user_data["password"]),
                user_status=UserStatus.ACTIVE.value,
            )
            session.add(user)
            await session.flush()

            # Asignar rol
            role_result = await session.execute(
                select(RoleModel).where(
                    RoleModel.name == user_data["role"]
                )
            )
            role = role_result.scalar_one_or_none()
            if role:
                session.add(
                    UserRoleModel(
                        id=str(uuid4()),
                        fk_user_id=user.id,
                        fk_role_id=role.id,
                    )
                )

    async def clear(self, session: AsyncSession) -> None:
        from sqlalchemy import delete

        emails = [u["email"] for u in TEST_USERS]
        users = await session.execute(
            select(UserModel).where(UserModel.email.in_(emails))
        )
        user_ids = [u.id for u in users.scalars()]

        if user_ids:
            await session.execute(
                delete(UserRoleModel).where(
                    UserRoleModel.fk_user_id.in_(user_ids)
                )
            )
        await session.execute(
            delete(UserModel).where(UserModel.email.in_(emails))
        )
