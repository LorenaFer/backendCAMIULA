"""SQLAlchemy implementation of the AvailabilityReader interface.

Consumed by the appointments module via DI (dependencies.py).
"""

from datetime import date
from typing import List, Set

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.doctors.domain.repositories.availability_reader import (
    AvailabilityBlock,
    AvailabilityReader,
)
from app.modules.doctors.infrastructure.models import (
    DoctorAvailabilityModel,
    DoctorExceptionModel,
)
from app.shared.database.mixins import RecordStatus


class SQLAlchemyAvailabilityReader(AvailabilityReader):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_blocks(
        self, doctor_id: str, day_of_week: int
    ) -> List[AvailabilityBlock]:
        result = await self._session.execute(
            select(DoctorAvailabilityModel).where(
                DoctorAvailabilityModel.fk_doctor_id == doctor_id,
                DoctorAvailabilityModel.day_of_week == day_of_week,
                DoctorAvailabilityModel.status == RecordStatus.ACTIVE,
            )
        )
        return [
            AvailabilityBlock(
                id=m.id,
                fk_doctor_id=m.fk_doctor_id,
                day_of_week=m.day_of_week,
                start_time=m.start_time,
                end_time=m.end_time,
                slot_duration=m.slot_duration,
            )
            for m in result.scalars().all()
        ]

    async def has_exception(self, doctor_id: str, target_date: date) -> bool:
        result = await self._session.execute(
            select(DoctorExceptionModel).where(
                DoctorExceptionModel.fk_doctor_id == doctor_id,
                DoctorExceptionModel.exception_date == target_date,
                DoctorExceptionModel.status == RecordStatus.ACTIVE,
            )
        )
        return result.scalar_one_or_none() is not None

    async def get_available_dows(self, doctor_id: str) -> Set[int]:
        result = await self._session.execute(
            select(DoctorAvailabilityModel.day_of_week).distinct().where(
                DoctorAvailabilityModel.fk_doctor_id == doctor_id,
                DoctorAvailabilityModel.status == RecordStatus.ACTIVE,
            )
        )
        return {row[0] for row in result.all()}

    async def get_exception_dates(
        self, doctor_id: str, start: date, end: date
    ) -> Set[date]:
        result = await self._session.execute(
            select(DoctorExceptionModel.exception_date).where(
                DoctorExceptionModel.fk_doctor_id == doctor_id,
                DoctorExceptionModel.exception_date >= start,
                DoctorExceptionModel.exception_date <= end,
                DoctorExceptionModel.status == RecordStatus.ACTIVE,
            )
        )
        return {row[0] for row in result.all()}
