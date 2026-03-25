from app.core.exceptions import ConflictException
from app.modules.appointments.application.dtos.availability_dto import CreateAvailabilityBlockDTO
from app.modules.appointments.domain.entities.availability import DoctorAvailability
from app.modules.appointments.domain.repositories.availability_repository import AvailabilityRepository


class CreateAvailabilityBlockUseCase:
    """Crea un bloque de disponibilidad. Valida solapamiento.

    Complejidad: O(log n) — verificación de overlap con índice compuesto.
    """

    def __init__(self, availability_repo: AvailabilityRepository) -> None:
        self._repo = availability_repo

    async def execute(self, dto: CreateAvailabilityBlockDTO) -> DoctorAvailability:
        block = DoctorAvailability(
            doctor_id=dto.doctor_id,
            day_of_week=dto.day_of_week,
            start_time=dto.start_time,
            end_time=dto.end_time,
            slot_duration=dto.slot_duration,
        )
        block.validate()

        if await self._repo.check_overlap(
            doctor_id=dto.doctor_id,
            day_of_week=dto.day_of_week,
            start_time=dto.start_time,
            end_time=dto.end_time,
        ):
            raise ConflictException("El bloque se solapa con otro existente")

        return await self._repo.create_block(block)
