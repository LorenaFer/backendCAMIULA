"""Use case: check if a slot is occupied."""

from app.modules.appointments.domain.repositories.appointment_repository import (
    AppointmentRepository,
)


class CheckSlot:
    def __init__(self, repo: AppointmentRepository) -> None:
        self._repo = repo

    async def execute(self, doctor_id: str, fecha: str, hora_inicio: str) -> bool:
        """Returns True if the slot is occupied (double-booked)."""
        return await self._repo.check_double_booking(
            doctor_id=doctor_id,
            fecha=fecha,
            start_time=hora_inicio,
        )
