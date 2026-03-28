from __future__ import annotations

from datetime import date, datetime, time, timezone
from typing import List, Optional
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.appointments.domain.entities.availability import (
    DoctorAvailability,
    DoctorException,
)
from app.modules.appointments.domain.repositories.availability_repository import (
    AvailabilityRepository,
)
from app.modules.appointments.infrastructure.models import (
    DoctorAvailabilityModel,
    DoctorExceptionModel,
)
from app.shared.database.mixins import RecordStatus


class SQLAlchemyAvailabilityRepository(AvailabilityRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _to_entity(model: DoctorAvailabilityModel) -> DoctorAvailability:
        return DoctorAvailability(
            id=model.id,
            doctor_id=model.fk_doctor_id,
            day_of_week=model.day_of_week,
            start_time=model.start_time,
            end_time=model.end_time,
            slot_duration=model.slot_duration,
        )

    async def list_by_doctor(
        self, doctor_id: str, day_of_week: Optional[int] = None
    ) -> List[DoctorAvailability]:
        stmt = select(DoctorAvailabilityModel).where(
            DoctorAvailabilityModel.fk_doctor_id == doctor_id,
            DoctorAvailabilityModel.status == RecordStatus.ACTIVE,
        )
        if day_of_week is not None:
            stmt = stmt.where(DoctorAvailabilityModel.day_of_week == day_of_week)
        stmt = stmt.order_by(
            DoctorAvailabilityModel.day_of_week,
            DoctorAvailabilityModel.start_time,
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars()]

    async def create_block(self, block: DoctorAvailability) -> DoctorAvailability:
        model = DoctorAvailabilityModel(
            id=block.id or str(uuid4()),
            fk_doctor_id=block.doctor_id,
            day_of_week=block.day_of_week,
            start_time=block.start_time,
            end_time=block.end_time,
            slot_duration=block.slot_duration,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_entity(model)

    async def get_block_by_id(self, block_id: str) -> Optional[DoctorAvailability]:
        stmt = select(DoctorAvailabilityModel).where(
            DoctorAvailabilityModel.id == block_id,
            DoctorAvailabilityModel.status == RecordStatus.ACTIVE,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def update_block(self, block: DoctorAvailability) -> DoctorAvailability:
        stmt = select(DoctorAvailabilityModel).where(
            DoctorAvailabilityModel.id == block.id
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            raise ValueError(f"Block {block.id} not found")
        model.start_time = block.start_time
        model.end_time = block.end_time
        await self._session.flush()
        return self._to_entity(model)

    async def delete_block(self, block_id: str, deleted_by: str) -> None:
        """Soft-delete: status -> T."""
        stmt = select(DoctorAvailabilityModel).where(
            DoctorAvailabilityModel.id == block_id
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            model.status = RecordStatus.TRASH
            model.deleted_at = datetime.now(timezone.utc)
            model.deleted_by = deleted_by
            await self._session.flush()

    async def check_overlap(
        self,
        doctor_id: str,
        day_of_week: int,
        start_time: time,
        end_time: time,
        exclude_id: Optional[str] = None,
    ) -> bool:
        """O(log n) con índice compuesto (fk_doctor_id, day_of_week)."""
        stmt = (
            select(func.count())
            .select_from(DoctorAvailabilityModel)
            .where(
                DoctorAvailabilityModel.fk_doctor_id == doctor_id,
                DoctorAvailabilityModel.day_of_week == day_of_week,
                DoctorAvailabilityModel.start_time < end_time,
                DoctorAvailabilityModel.end_time > start_time,
                DoctorAvailabilityModel.status == RecordStatus.ACTIVE,
            )
        )
        if exclude_id:
            stmt = stmt.where(DoctorAvailabilityModel.id != exclude_id)
        result = await self._session.execute(stmt)
        return result.scalar_one() > 0

    async def has_exception(self, doctor_id: str, check_date: date) -> bool:
        """O(log n) con índice compuesto (fk_doctor_id, exception_date)."""
        stmt = (
            select(func.count())
            .select_from(DoctorExceptionModel)
            .where(
                DoctorExceptionModel.fk_doctor_id == doctor_id,
                DoctorExceptionModel.exception_date == check_date,
                DoctorExceptionModel.status == RecordStatus.ACTIVE,
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one() > 0
