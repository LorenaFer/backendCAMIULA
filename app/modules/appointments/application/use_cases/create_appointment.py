"""Use case: create appointment with double-booking validation."""

from app.core.exceptions import ConflictException
from app.modules.appointments.application.dtos.appointment_dto import (
    CreateAppointmentDTO,
)
from app.modules.appointments.domain.entities.appointment import Appointment
from app.modules.appointments.domain.repositories.appointment_repository import (
    AppointmentRepository,
)


class CreateAppointment:
    def __init__(self, repo: AppointmentRepository) -> None:
        self._repo = repo

    async def execute(self, dto: CreateAppointmentDTO, created_by: str) -> Appointment:
        # Validate double-booking: same doctor + date + start_time, non-cancelled
        is_booked = await self._repo.check_double_booking(
            doctor_id=dto.fk_doctor_id,
            date_str=dto.appointment_date,
            start_time=dto.start_time,
        )
        if is_booked:
            raise ConflictException(
                "An appointment already exists for this doctor at the same date and time."
            )

        data = {
            "fk_patient_id": dto.fk_patient_id,
            "fk_doctor_id": dto.fk_doctor_id,
            "fk_specialty_id": dto.fk_specialty_id,
            "appointment_date": dto.appointment_date,
            "start_time": dto.start_time,
            "end_time": dto.end_time,
            "duration_minutes": dto.duration_minutes,
            "is_first_visit": dto.is_first_visit,
            "reason": dto.reason,
            "observations": dto.observations,
            "appointment_status": "pendiente",
        }
        return await self._repo.create(data, created_by)
