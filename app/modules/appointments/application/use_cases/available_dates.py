"""Use case: compute available dates for a doctor in a given month."""

import calendar
from datetime import date as date_type, timedelta
from typing import List

from app.modules.doctors.domain.repositories.availability_reader import (
    AvailabilityReader,
)


class AvailableDates:
    def __init__(self, availability_reader: AvailabilityReader) -> None:
        self._availability = availability_reader

    async def execute(self, doctor_id: str, year: int, month: int) -> List[str]:
        # Get doctor's availability blocks (distinct day_of_week)
        available_dows = await self._availability.get_available_dows(doctor_id)

        if not available_dows:
            return []

        # Get exceptions for this month
        first_day = date_type(year, month, 1)
        last_day = date_type(year, month, calendar.monthrange(year, month)[1])
        exception_dates = await self._availability.get_exception_dates(
            doctor_id, first_day, last_day
        )

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
