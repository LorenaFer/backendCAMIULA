"""Use case: get appointment by ID."""

from app.core.exceptions import NotFoundException
from app.modules.appointments.domain.entities.appointment import Appointment
from app.modules.appointments.domain.repositories.appointment_repository import (
    AppointmentRepository,
)


class GetAppointment:
    def __init__(self, repo: AppointmentRepository) -> None:
        self._repo = repo

    async def execute(self, appointment_id: str) -> Appointment:
        appointment = await self._repo.find_by_id(appointment_id)
        if not appointment:
            raise NotFoundException("Cita no encontrada")
        return appointment
