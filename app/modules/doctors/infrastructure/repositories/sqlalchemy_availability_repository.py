"""SQLAlchemy implementation of the Availability repository."""

from datetime import datetime, timezone
from typing import List, Optional
from uuid import uuid4

from sqlalchemy import select, update as sql_update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.doctors.domain.entities.availability import DoctorAvailability
from app.modules.doctors.domain.repositories.availability_repository import (
    AvailabilityRepository,
)
from app.modules.doctors.infrastructure.models import DoctorAvailabilityModel
from app.shared.database.mixins import RecordStatus


class SQLAlchemyAvailabilityRepository(AvailabilityRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _to_entity(model: DoctorAvailabilityModel) -> DoctorAvailability:
        return DoctorAvailability(
            id=model.id,
            fk_doctor_id=model.fk_doctor_id,
            day_of_week=model.day_of_week,
            start_time=model.start_time,
            end_time=model.end_time,
            slot_duration=model.slot_duration,
            status=model.status if isinstance(model.status, str) else model.status.value,
            created_at=model.created_at.isoformat() if model.created_at else None,
            created_by=model.created_by,
        )

    async def find_by_doctor(
        self, doctor_id: str, day_of_week: Optional[int] = None
    ) -> List[DoctorAvailability]:
        q = (
            select(DoctorAvailabilityModel)
            .where(
                DoctorAvailabilityModel.fk_doctor_id == doctor_id,
                DoctorAvailabilityModel.status == RecordStatus.ACTIVE,
            )
            .order_by(
                DoctorAvailabilityModel.day_of_week,
                DoctorAvailabilityModel.start_time,
            )
        )
        if day_of_week is not None:
            q = q.where(DoctorAvailabilityModel.day_of_week == day_of_week)

        result = await self._session.execute(q)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def find_by_id(
        self, doctor_id: str, block_id: str
    ) -> Optional[DoctorAvailability]:
        result = await self._session.execute(
            select(DoctorAvailabilityModel).where(
                DoctorAvailabilityModel.id == block_id,
                DoctorAvailabilityModel.fk_doctor_id == doctor_id,
                DoctorAvailabilityModel.status == RecordStatus.ACTIVE,
            )
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def create(self, data: dict, created_by: str) -> DoctorAvailability:
        model = DoctorAvailabilityModel(
            id=str(uuid4()),
            created_by=created_by,
            **data,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def update(
        self, doctor_id: str, block_id: str, data: dict, updated_by: str
    ) -> None:
        data["updated_by"] = updated_by
        data["updated_at"] = datetime.now(timezone.utc)
        await self._session.execute(
            sql_update(DoctorAvailabilityModel)
            .where(
                DoctorAvailabilityModel.id == block_id,
                DoctorAvailabilityModel.fk_doctor_id == doctor_id,
            )
            .values(**data)
        )
        await self._session.flush()

    async def soft_delete(
        self, doctor_id: str, block_id: str, deleted_by: str
    ) -> None:
        await self._session.execute(
            sql_update(DoctorAvailabilityModel)
            .where(
                DoctorAvailabilityModel.id == block_id,
                DoctorAvailabilityModel.fk_doctor_id == doctor_id,
            )
            .values(
                status=RecordStatus.TRASH,
                deleted_at=datetime.now(timezone.utc),
                deleted_by=deleted_by,
            )
        )
        await self._session.flush()
