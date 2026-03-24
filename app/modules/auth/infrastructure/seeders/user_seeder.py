"""
Seeder de usuarios iniciales (admin, usuario de prueba).

Ejecutar:
    python -m app.shared.database.seeder auth
    python -m app.shared.database.seeder auth --fresh
"""

from uuid import uuid4

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.shared.database.seeder import BaseSeeder

# NOTA: Descomentar cuando el modelo UserModel exista:
# from app.modules.auth.infrastructure.models import UserModel


class UserSeeder(BaseSeeder):
    """Siembra usuarios iniciales para desarrollo/testing."""

    order = 10  # Se ejecuta temprano (otros módulos pueden depender de users)

    async def run(self, session: AsyncSession) -> None:
        # TODO: Descomentar cuando UserModel exista
        #
        # existing = await session.execute(
        #     select(UserModel).where(UserModel.email == "admin@camiula.com")
        # )
        # if existing.scalar_one_or_none():
        #     return  # Ya existe, no duplicar
        #
        # admin = UserModel(
        #     id=str(uuid4()),
        #     email="admin@camiula.com",
        #     full_name="Administrador CAMIULA",
        #     hashed_password=hash_password("admin123"),  # Solo para dev
        #     created_by=None,  # Auto-creado por seeder
        # )
        # session.add(admin)
        pass

    async def clear(self, session: AsyncSession) -> None:
        # TODO: Descomentar cuando UserModel exista
        #
        # await session.execute(
        #     delete(UserModel).where(UserModel.email == "admin@camiula.com")
        # )
        pass
