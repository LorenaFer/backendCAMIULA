from app.core.exceptions import NotFoundException
from app.modules.appointments.domain.entities.appointment import Appointment
from app.modules.appointments.domain.repositories.appointment_repository import AppointmentRepository


class GetAppointmentDetailUseCase:
    def __init__(self, appointment_repo: AppointmentRepository) -> None:
        self._repo = appointment_repo

    async def execute(self, appointment_id: str) -> Appointment:
        appointment = await self._repo.get_detail(appointment_id)
        if appointment is None:
            raise NotFoundException("Cita no encontrada")
        return appointment
