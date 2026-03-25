from app.core.exceptions import AppException, NotFoundException
from app.modules.appointments.application.dtos.appointment_dto import ChangeAppointmentStatusDTO
from app.modules.appointments.domain.repositories.appointment_repository import AppointmentRepository


class ChangeAppointmentStatusUseCase:
    def __init__(self, appointment_repo: AppointmentRepository) -> None:
        self._repo = appointment_repo

    async def execute(self, dto: ChangeAppointmentStatusDTO, updated_by: str) -> None:
        appointment = await self._repo.get_by_id(dto.appointment_id)
        if appointment is None:
            raise NotFoundException("Cita no encontrada")

        try:
            appointment.change_status(dto.new_status)
        except ValueError as e:
            raise AppException(str(e), status_code=422)

        await self._repo.update_status(dto.appointment_id, dto.new_status, updated_by)
