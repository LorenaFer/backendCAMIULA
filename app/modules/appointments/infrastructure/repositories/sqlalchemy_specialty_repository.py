from __future__ import annotations

from typing import List, Optional

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
        return Specialty(id=model.id, name=model.name)

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
            SpecialtyModel.status == RecordStatus.ACTIVE,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None
