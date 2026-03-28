from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.appointments.domain.entities.specialty import Specialty
from app.modules.appointments.domain.repositories.specialty_repository import (
    SpecialtyRepository,
)
from app.modules.appointments.infrastructure.models import SpecialtyModel
from app.shared.database.mixins import RecordStatus


class SQLAlchemySpecialtyRepository(SpecialtyRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _to_entity(model: SpecialtyModel) -> Specialty:
        return Specialty(
            id=model.id,
            name=model.name,
            is_active=model.status == RecordStatus.ACTIVE,
        )

    async def list_active(self) -> List[Specialty]:
        stmt = (
            select(SpecialtyModel)
            .where(SpecialtyModel.status == RecordStatus.ACTIVE)
            .order_by(SpecialtyModel.name)
            .limit(100)
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars()]

    async def get_by_id(self, specialty_id: str) -> Optional[Specialty]:
        stmt = select(SpecialtyModel).where(
            SpecialtyModel.id == specialty_id,
            SpecialtyModel.status != RecordStatus.TRASH,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_name(self, name: str) -> Optional[Specialty]:
        stmt = select(SpecialtyModel).where(
            SpecialtyModel.name == name,
            SpecialtyModel.status != RecordStatus.TRASH,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def create(self, specialty: Specialty, created_by: Optional[str] = None) -> Specialty:
        model = SpecialtyModel(
            id=specialty.id or str(uuid4()),
            name=specialty.name,
            created_by=created_by,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_entity(model)

    async def update(self, specialty: Specialty, updated_by: Optional[str] = None) -> Specialty:
        stmt = select(SpecialtyModel).where(SpecialtyModel.id == specialty.id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            model.name = specialty.name
            model.updated_by = updated_by
            model.updated_at = datetime.now(timezone.utc)
            await self._session.flush()
        return self._to_entity(model)

    async def toggle(self, specialty_id: str, updated_by: Optional[str] = None) -> Specialty:
        stmt = select(SpecialtyModel).where(SpecialtyModel.id == specialty_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            model.status = (
                RecordStatus.INACTIVE
                if model.status == RecordStatus.ACTIVE
                else RecordStatus.ACTIVE
            )
            model.updated_by = updated_by
            model.updated_at = datetime.now(timezone.utc)
            await self._session.flush()
        return self._to_entity(model)
