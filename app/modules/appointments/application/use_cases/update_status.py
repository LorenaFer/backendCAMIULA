"""Use case: update appointment status with state machine validation."""

from app.core.exceptions import AppException, NotFoundException
from app.modules.appointments.domain.entities.appointment import Appointment
from app.modules.appointments.domain.repositories.appointment_repository import (
    AppointmentRepository,
)

# State machine transitions
# Accepts both English and Spanish status names
# pendiente/pending can go directly to atendida/attended (walk-in/emergency)
VALID_TRANSITIONS = {
    "pendiente": {"confirmada", "cancelada", "atendida", "no_asistio", "confirmed", "cancelled", "attended", "no_show"},
    "confirmada": {"atendida", "cancelada", "no_asistio", "attended", "cancelled", "no_show"},
    "confirmed": {"attended", "cancelled", "no_show", "atendida", "cancelada", "no_asistio"},
    "pending": {"confirmed", "cancelled", "attended", "no_show", "confirmada", "cancelada", "atendida", "no_asistio"},
}


class UpdateAppointmentStatus:
    def __init__(self, repo: AppointmentRepository) -> None:
        self._repo = repo

    async def execute(
        self, appointment_id: str, new_status: str, updated_by: str
    ) -> Appointment:
        appointment = await self._repo.find_by_id(appointment_id)
        if not appointment:
            raise NotFoundException("Cita no encontrada")

        current = appointment.appointment_status
        allowed = VALID_TRANSITIONS.get(current, set())

        if new_status not in allowed:
            raise AppException(
                f"Transicion invalida: '{current}' -> '{new_status}'. "
                f"Transiciones permitidas desde '{current}': {sorted(allowed) if allowed else 'ninguna'}",
                status_code=400,
            )

        return await self._repo.update_status(appointment_id, new_status, updated_by)
