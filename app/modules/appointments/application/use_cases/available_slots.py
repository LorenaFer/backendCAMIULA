"""Use case: compute available time slots for a doctor on a given date."""

from datetime import date as date_type
from datetime import time as time_type
from typing import Any, Dict, List

from app.modules.appointments.domain.repositories.appointment_repository import (
    AppointmentRepository,
)
from app.modules.doctors.domain.repositories.availability_reader import (
    AvailabilityReader,
)


class AvailableSlots:
    def __init__(
        self,
        repo: AppointmentRepository,
        availability_reader: AvailabilityReader,
    ) -> None:
        self._repo = repo
        self._availability = availability_reader

    async def execute(
        self, doctor_id: str, date_str: str, es_nuevo: bool
    ) -> List[Dict[str, Any]]:
        target_date = date_type.fromisoformat(date_str)
        dow = target_date.isoweekday()  # 1=Mon ... 7=Sun

        # 1. Get availability blocks for this day_of_week
        blocks = await self._availability.get_blocks(doctor_id, dow)
        if not blocks:
            return []

        # 2. Check for exception on this date
        if await self._availability.has_exception(doctor_id, target_date):
            return []

        # 3. Get existing non-cancelled appointments
        existing = await self._repo.find_non_cancelled_by_doctor_and_date(
            doctor_id, date_str
        )

        # 4. Duration based on es_nuevo
        duration = 60 if es_nuevo else 30
        slot_step = blocks[0].slot_duration if blocks else 30

        # 5. Generate slots
        slots = []
        for block in blocks:
            block_start = _to_minutes(block.start_time)
            block_end = _to_minutes(block.end_time)

            current = block_start
            while current + duration <= block_end:
                slot_start_str = _minutes_to_hhmm(current)
                slot_end_str = _minutes_to_hhmm(current + duration)

                # 6. Check overlap with existing appointments
                available = True
                for appt in existing:
                    appt_start = _to_minutes(appt.start_time)
                    appt_end = _to_minutes(appt.end_time)
                    if current < appt_end and (current + duration) > appt_start:
                        available = False
                        break

                slots.append({
                    "start_time": slot_start_str,
                    "end_time": slot_end_str,
                    "available": available,
                })
                current += slot_step

        return slots


def _to_minutes(t) -> int:
    """Convert time object or 'HH:MM' string to minutes since midnight."""
    if isinstance(t, time_type):
        return t.hour * 60 + t.minute
    if isinstance(t, str):
        parts = t.split(":")
        return int(parts[0]) * 60 + int(parts[1])
    return 0


def _minutes_to_hhmm(minutes: int) -> str:
    """Convert minutes since midnight to 'HH:MM'."""
    return f"{minutes // 60:02d}:{minutes % 60:02d}"
