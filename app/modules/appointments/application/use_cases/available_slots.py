"""Use case: compute available time slots for a doctor on a given date."""

from datetime import date as date_type
from typing import Any, Dict, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.appointments.domain.repositories.appointment_repository import (
    AppointmentRepository,
)
from app.modules.doctors.infrastructure.models import (
    DoctorAvailabilityModel,
    DoctorExceptionModel,
)
from app.shared.database.mixins import RecordStatus


class AvailableSlots:
    def __init__(self, repo: AppointmentRepository, session: AsyncSession) -> None:
        self._repo = repo
        self._session = session

    async def execute(
        self, doctor_id: str, fecha: str, es_nuevo: bool
    ) -> List[Dict[str, Any]]:
        target_date = date_type.fromisoformat(fecha)
        dow = target_date.isoweekday()  # 1=Mon ... 7=Sun

        # 1. Get availability blocks for this day_of_week
        avail_result = await self._session.execute(
            select(DoctorAvailabilityModel).where(
                DoctorAvailabilityModel.fk_doctor_id == doctor_id,
                DoctorAvailabilityModel.day_of_week == dow,
                DoctorAvailabilityModel.status == RecordStatus.ACTIVE,
            )
        )
        blocks = avail_result.scalars().all()

        if not blocks:
            return []

        # 2. Check for exception on this date
        exc_result = await self._session.execute(
            select(DoctorExceptionModel).where(
                DoctorExceptionModel.fk_doctor_id == doctor_id,
                DoctorExceptionModel.exception_date == target_date,
                DoctorExceptionModel.status == RecordStatus.ACTIVE,
            )
        )
        if exc_result.scalar_one_or_none():
            return []

        # 3. Get existing non-cancelled appointments
        existing = await self._repo.find_non_cancelled_by_doctor_and_date(
            doctor_id, fecha
        )

        # 4. Duration based on es_nuevo
        duration = 60 if es_nuevo else 30

        # 5. Generate slots
        slots = []
        for block in blocks:
            block_start = _time_to_minutes(block.start_time)
            block_end = _time_to_minutes(block.end_time)

            current = block_start
            while current + duration <= block_end:
                slot_start = _minutes_to_time(current)
                slot_end = _minutes_to_time(current + duration)

                # 6. Check overlap with existing appointments
                available = True
                for appt in existing:
                    appt_start = _time_to_minutes(appt.start_time)
                    appt_end = _time_to_minutes(appt.end_time)
                    # Overlap: slot_start < appt_end AND slot_end > appt_start
                    if current < appt_end and (current + duration) > appt_start:
                        available = False
                        break

                slots.append({
                    "start_time": slot_start,
                    "end_time": slot_end,
                    "available": available,
                })
                current += duration

        return slots


def _time_to_minutes(t: str) -> int:
    """Convert 'HH:MM' to minutes since midnight."""
    h, m = t.split(":")
    return int(h) * 60 + int(m)


def _minutes_to_time(minutes: int) -> str:
    """Convert minutes since midnight to 'HH:MM'."""
    h = minutes // 60
    m = minutes % 60
    return f"{h:02d}:{m:02d}"
