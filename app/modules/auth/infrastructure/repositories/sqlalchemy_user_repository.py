from __future__ import annotations

from typing import Optional, Set, Tuple
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.domain.entities.enums import UserStatus
from app.modules.auth.domain.entities.user import User
from app.modules.auth.domain.repositories.user_repository import UserRepository
from app.modules.auth.infrastructure.models import (
    PermissionModel,
    RoleModel,
    RolePermissionModel,
    UserModel,
    UserRoleModel,
)
from app.shared.database.mixins import RecordStatus


class SQLAlchemyUserRepository(UserRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # -- Mapeo entity ↔ model --

    @staticmethod
    def _to_entity(model: UserModel) -> User:
        return User(
            id=model.id,
            email=model.email,
            full_name=model.full_name,
            external_auth=model.external_auth,
            phone=model.phone,
            cedula=model.cedula,
            username=model.username,
            hashed_password=model.hashed_password,
            user_status=model.user_status or UserStatus.PENDING.value,
        )

    # -- CRUD --

    async def create(self, user: User) -> User:
        model = UserModel(
            id=user.id or str(uuid4()),
            external_auth=user.external_auth,
            email=user.email,
            full_name=user.full_name,
            phone=user.phone,
            cedula=user.cedula,
            username=user.username,
            hashed_password=user.hashed_password,
            user_status=user.user_status,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_entity(model)

    async def get_by_id(self, user_id: str) -> Optional[User]:
        stmt = select(UserModel).where(
            UserModel.id == user_id,
            UserModel.status == RecordStatus.ACTIVE,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_email(self, email: str) -> Optional[User]:
        stmt = select(UserModel).where(
            UserModel.email == email,
            UserModel.status == RecordStatus.ACTIVE,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_cedula(self, cedula: str) -> Optional[User]:
        stmt = select(UserModel).where(
            UserModel.cedula == cedula,
            UserModel.status == RecordStatus.ACTIVE,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_username(self, username: str) -> Optional[User]:
        stmt = select(UserModel).where(
            UserModel.username == username,
            UserModel.status == RecordStatus.ACTIVE,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_external_sub(
        self, provider: str, sub: str
    ) -> Optional[User]:
        """Busca por sub dentro del JSONB external_auth.

        Query: WHERE external_auth->'provider'->>'sub' = sub
        PostgreSQL usa GIN index en JSONB para O(log n).
        """
        stmt = select(UserModel).where(
            UserModel.external_auth[provider]["sub"].astext == sub,
            UserModel.status == RecordStatus.ACTIVE,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def update(self, user: User) -> User:
        stmt = select(UserModel).where(UserModel.id == user.id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            raise ValueError(f"User {user.id} not found")

        model.full_name = user.full_name
        model.phone = user.phone
        model.user_status = user.user_status
        await self._session.flush()
        return self._to_entity(model)

    async def list_paginated(
        self, page: int, page_size: int
    ) -> Tuple[list[User], int]:
        # COUNT — O(log n) con índice en status
        count_stmt = (
            select(func.count())
            .select_from(UserModel)
            .where(UserModel.status == RecordStatus.ACTIVE)
        )
        total = (await self._session.execute(count_stmt)).scalar_one()

        # SELECT — O(log n + k) con k = page_size
        stmt = (
            select(UserModel)
            .where(UserModel.status == RecordStatus.ACTIVE)
            .order_by(UserModel.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self._session.execute(stmt)
        users = [self._to_entity(m) for m in result.scalars()]
        return users, total

    # -- Permisos y roles --

    async def get_user_permissions(self, user_id: str) -> Set[str]:
        """Un solo query con JOINs — O(log n) con índices compuestos."""
        stmt = (
            select(PermissionModel.code)
            .join(
                RolePermissionModel,
                RolePermissionModel.fk_permission_id == PermissionModel.id,
            )
            .join(
                UserRoleModel,
                UserRoleModel.fk_role_id == RolePermissionModel.fk_role_id,
            )
            .where(
                UserRoleModel.fk_user_id == user_id,
                UserRoleModel.status == RecordStatus.ACTIVE,
                RolePermissionModel.status == RecordStatus.ACTIVE,
                PermissionModel.status == RecordStatus.ACTIVE,
            )
        )
        result = await self._session.execute(stmt)
        return set(result.scalars().all())

    async def get_user_roles(self, user_id: str) -> list[str]:
        stmt = (
            select(RoleModel.name)
            .join(
                UserRoleModel,
                UserRoleModel.fk_role_id == RoleModel.id,
            )
            .where(
                UserRoleModel.fk_user_id == user_id,
                UserRoleModel.status == RecordStatus.ACTIVE,
                RoleModel.status == RecordStatus.ACTIVE,
            )
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
