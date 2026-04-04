from __future__ import annotations

from typing import Optional, Set, Tuple
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

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
            hashed_password=model.hashed_password,
            user_status=model.user_status or "PENDING",
        )

    # -- CRUD --

    async def create(self, user: User) -> User:
        model = UserModel(
            id=user.id or str(uuid4()),
            external_auth=user.external_auth,
            email=user.email,
            full_name=user.full_name,
            phone=user.phone,
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
        self,
        page: int,
        page_size: int,
        search: Optional[str] = None,
        role: Optional[str] = None,
        exclude_only_role: Optional[str] = None,
    ) -> Tuple[list[User], int]:
        """List users with optional search and role filters.

        - search: filter by email or full_name (ILIKE)
        - role: only users with this role
        - exclude_only_role: exclude users whose ONLY role is this one
        """
        base = (
            select(UserModel)
            .where(UserModel.status == RecordStatus.ACTIVE)
        )

        if search:
            pattern = f"%{search}%"
            from sqlalchemy import or_
            base = base.where(
                or_(
                    UserModel.email.ilike(pattern),
                    UserModel.full_name.ilike(pattern),
                )
            )

        if role:
            base = base.join(
                UserRoleModel, UserRoleModel.fk_user_id == UserModel.id
            ).join(
                RoleModel, RoleModel.id == UserRoleModel.fk_role_id
            ).where(RoleModel.name == role)

        if exclude_only_role:
            # Exclude users who have ONLY this role (no other roles)
            has_other_role = (
                select(UserRoleModel.fk_user_id)
                .join(RoleModel, RoleModel.id == UserRoleModel.fk_role_id)
                .where(RoleModel.name != exclude_only_role)
                .subquery()
            )
            base = base.where(UserModel.id.in_(select(has_other_role.c.fk_user_id)))

        count_stmt = select(func.count()).select_from(base.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = (
            base.order_by(UserModel.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self._session.execute(stmt)
        users = [self._to_entity(m) for m in result.unique().scalars()]
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
