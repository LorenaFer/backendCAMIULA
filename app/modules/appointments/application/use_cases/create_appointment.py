from app.core.exceptions import AppException, ConflictException
from app.modules.appointments.application.dtos.appointment_dto import CreateAppointmentDTO
from app.modules.appointments.domain.entities.appointment import Appointment
from app.modules.appointments.domain.repositories.appointment_repository import AppointmentRepository
from app.modules.appointments.domain.repositories.availability_repository import AvailabilityRepository


class CreateAppointmentUseCase:
    """Crea una cita validando todas las reglas de negocio.

    Validaciones:
    - Fecha >= hoy + 2 días
    - Duración correcta según tipo (30/60 min)
    - Slot no ocupado (sin doble reserva)
    - Doctor tiene disponibilidad en ese día/hora
    - Doctor no tiene excepción en esa fecha

    Complejidad: O(log n) — cada verificación usa índices.
    """

    def __init__(
        self,
        appointment_repo: AppointmentRepository,
        availability_repo: AvailabilityRepository,
    ) -> None:
        self._appointment_repo = appointment_repo
        self._availability_repo = availability_repo

    async def execute(self, dto: CreateAppointmentDTO, created_by: str) -> Appointment:
        appointment = Appointment(
            patient_id=dto.patient_id,
            doctor_id=dto.doctor_id,
            specialty_id=dto.specialty_id,
            appointment_date=dto.appointment_date,
            start_time=dto.start_time,
            end_time=dto.end_time,
            duration_minutes=dto.duration_minutes,
            is_first_visit=dto.is_first_visit,
            reason=dto.reason,
            observations=dto.observations,
            created_by=created_by,
        )

        # Validar fecha mínima
        appointment.validate_date()

        # Validar duración según tipo de visita
        appointment.validate_duration()

        # Verificar excepción del doctor
        if await self._availability_repo.has_exception(dto.doctor_id, dto.appointment_date):
            raise AppException(
                "El doctor no atiende en esta fecha (día de excepción)", status_code=409
            )

        # Verificar disponibilidad del doctor en ese día/hora
        day_of_week = dto.appointment_date.isoweekday()  # 1=Lun, 7=Dom
        blocks = await self._availability_repo.list_by_doctor(dto.doctor_id, day_of_week)
        if not blocks:
            raise AppException(
                "El doctor no tiene disponibilidad configurada para este día",
                status_code=409,
            )

        # Verificar que la hora cae dentro de algún bloque
        in_block = any(
            b.start_time <= dto.start_time and dto.end_time <= b.end_time
            for b in blocks
        )
        if not in_block:
            raise AppException(
                "El horario no corresponde a la disponibilidad del doctor",
                status_code=409,
            )

        # Verificar slot no ocupado
        if await self._appointment_repo.is_slot_occupied(
            doctor_id=dto.doctor_id,
            appointment_date=dto.appointment_date,
            start_time=dto.start_time,
            end_time=dto.end_time,
        ):
            raise ConflictException(
                "Este horario ya fue tomado. Por favor seleccione otro."
            )

        return await self._appointment_repo.create(appointment)
