"""Use case: compute available dates for a doctor in a given month."""

import calendar
from datetime import date as date_type, timedelta
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.doctors.infrastructure.models import (
    DoctorAvailabilityModel,
    DoctorExceptionModel,
)
from app.shared.database.mixins import RecordStatus


class AvailableDates:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(self, doctor_id: str, year: int, month: int) -> List[str]:
        # Get doctor's availability blocks (distinct day_of_week)
        avail_result = await self._session.execute(
            select(DoctorAvailabilityModel.day_of_week).distinct().where(
                DoctorAvailabilityModel.fk_doctor_id == doctor_id,
                DoctorAvailabilityModel.status == RecordStatus.ACTIVE,
            )
        )
        available_dows = {row[0] for row in avail_result.all()}

        if not available_dows:
            return []

        # Get exceptions for this month
        first_day = date_type(year, month, 1)
        last_day = date_type(year, month, calendar.monthrange(year, month)[1])
        exc_result = await self._session.execute(
            select(DoctorExceptionModel.exception_date).where(
                DoctorExceptionModel.fk_doctor_id == doctor_id,
                DoctorExceptionModel.exception_date >= first_day,
                DoctorExceptionModel.exception_date <= last_day,
                DoctorExceptionModel.status == RecordStatus.ACTIVE,
            )
        )
        exception_dates = {row[0] for row in exc_result.all()}

        today = date_type.today()
        min_date = today + timedelta(days=2)

        dates = []
        current = first_day
        while current <= last_day:
            dow = current.isoweekday()  # 1=Mon ... 7=Sun

            # Skip weekends
            if dow > 5:
                current += timedelta(days=1)
                continue

            # Skip dates < today + 2
            if current < min_date:
                current += timedelta(days=1)
                continue

            # Check doctor has availability for this day_of_week
            if dow not in available_dows:
                current += timedelta(days=1)
                continue

            # Check no exception
            if current in exception_dates:
                current += timedelta(days=1)
                continue

            dates.append(current.isoformat())
            current += timedelta(days=1)

        return dates
