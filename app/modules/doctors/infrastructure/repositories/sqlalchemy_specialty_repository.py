"""SQLAlchemy implementation of the Specialty repository."""

from datetime import datetime, timezone
from typing import List, Optional
from uuid import uuid4

from sqlalchemy import select, update as sql_update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.doctors.domain.entities.specialty import Specialty
from app.modules.doctors.domain.repositories.specialty_repository import (
    SpecialtyRepository,
)
from app.modules.doctors.infrastructure.models import SpecialtyModel
from app.shared.database.mixins import RecordStatus


class SQLAlchemySpecialtyRepository(SpecialtyRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _to_entity(model: SpecialtyModel) -> Specialty:
        return Specialty(
            id=model.id,
            name=model.name,
            status=model.status if isinstance(model.status, str) else model.status.value,
            created_at=model.created_at.isoformat() if model.created_at else None,
            created_by=model.created_by,
        )

    async def find_all(self) -> List[Specialty]:
        result = await self._session.execute(
            select(SpecialtyModel)
            .where(SpecialtyModel.status != RecordStatus.TRASH)
            .order_by(SpecialtyModel.name)
        )
        return [self._to_entity(m) for m in result.scalars().all()]

    async def find_by_id(self, id: str) -> Optional[Specialty]:
        result = await self._session.execute(
            select(SpecialtyModel).where(
                SpecialtyModel.id == id,
                SpecialtyModel.status != RecordStatus.TRASH,
            )
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def find_by_name(self, name: str) -> Optional[Specialty]:
        result = await self._session.execute(
            select(SpecialtyModel).where(
                SpecialtyModel.name == name,
                SpecialtyModel.status != RecordStatus.TRASH,
            )
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def create(self, data: dict, created_by: str) -> Specialty:
        model = SpecialtyModel(
            id=str(uuid4()),
            created_by=created_by,
            **data,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def update(self, id: str, data: dict, updated_by: str) -> Specialty:
        data["updated_by"] = updated_by
        data["updated_at"] = datetime.now(timezone.utc)
        await self._session.execute(
            sql_update(SpecialtyModel)
            .where(SpecialtyModel.id == id)
            .values(**data)
        )
        await self._session.flush()
        return await self.find_by_id(id)

    async def toggle_status(self, id: str, updated_by: str) -> Specialty:
        result = await self._session.execute(
            select(SpecialtyModel).where(SpecialtyModel.id == id)
        )
        model = result.scalar_one_or_none()
        if not model:
            return None

        current = model.status if isinstance(model.status, str) else model.status.value
        new_status = RecordStatus.INACTIVE if current == RecordStatus.ACTIVE.value else RecordStatus.ACTIVE

        await self._session.execute(
            sql_update(SpecialtyModel)
            .where(SpecialtyModel.id == id)
            .values(
                status=new_status,
                updated_by=updated_by,
                updated_at=datetime.now(timezone.utc),
            )
        )
        await self._session.flush()
        return await self.find_by_id(id)
