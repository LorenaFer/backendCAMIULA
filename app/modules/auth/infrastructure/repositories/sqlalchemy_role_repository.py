from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.domain.entities.role import Role
from app.modules.auth.domain.repositories.role_repository import RoleRepository
from app.modules.auth.infrastructure.models import (
    PermissionModel,
    RoleModel,
    RolePermissionModel,
    UserRoleModel,
)
from app.shared.database.mixins import RecordStatus


class SQLAlchemyRoleRepository(RoleRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _to_entity(model: RoleModel, permissions: list[str] = None) -> Role:
        return Role(
            id=model.id,
            name=model.name,
            description=model.description,
            permissions=permissions or [],
        )

    async def _load_permissions(self, role_id: str) -> list[str]:
        stmt = (
            select(PermissionModel.code)
            .join(
                RolePermissionModel,
                RolePermissionModel.fk_permission_id == PermissionModel.id,
            )
            .where(
                RolePermissionModel.fk_role_id == role_id,
                RolePermissionModel.status == RecordStatus.ACTIVE,
                PermissionModel.status == RecordStatus.ACTIVE,
            )
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_name(self, name: str) -> Optional[Role]:
        stmt = select(RoleModel).where(
            RoleModel.name == name,
            RoleModel.status == RecordStatus.ACTIVE,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        perms = await self._load_permissions(model.id)
        return self._to_entity(model, perms)

    async def get_by_id(self, role_id: str) -> Optional[Role]:
        stmt = select(RoleModel).where(
            RoleModel.id == role_id,
            RoleModel.status == RecordStatus.ACTIVE,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        perms = await self._load_permissions(model.id)
        return self._to_entity(model, perms)

    async def list_all(self) -> list[Role]:
        stmt = (
            select(RoleModel)
            .where(RoleModel.status == RecordStatus.ACTIVE)
            .order_by(RoleModel.name)
        )
        result = await self._session.execute(stmt)
        roles = []
        for model in result.scalars():
            perms = await self._load_permissions(model.id)
            roles.append(self._to_entity(model, perms))
        return roles

    async def assign_role_to_user(
        self, user_id: str, role_id: str, assigned_by: Optional[str] = None
    ) -> None:
        junction = UserRoleModel(
            id=str(uuid4()),
            fk_user_id=user_id,
            fk_role_id=role_id,
            created_by=assigned_by,
        )
        self._session.add(junction)
        await self._session.flush()

    async def remove_role_from_user(
        self, user_id: str, role_id: str, removed_by: Optional[str] = None
    ) -> None:
        stmt = select(UserRoleModel).where(
            UserRoleModel.fk_user_id == user_id,
            UserRoleModel.fk_role_id == role_id,
            UserRoleModel.status == RecordStatus.ACTIVE,
        )
        result = await self._session.execute(stmt)
        junction = result.scalar_one_or_none()
        if junction:
            junction.status = RecordStatus.TRASH
            junction.deleted_at = datetime.now(timezone.utc)
            junction.deleted_by = removed_by
            await self._session.flush()
