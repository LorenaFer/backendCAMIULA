from app.core.exceptions import ConflictException, NotFoundException
from app.modules.appointments.application.dtos.availability_dto import UpdateAvailabilityBlockDTO
from app.modules.appointments.domain.entities.availability import DoctorAvailability
from app.modules.appointments.domain.repositories.availability_repository import AvailabilityRepository


class UpdateAvailabilityBlockUseCase:
    def __init__(self, availability_repo: AvailabilityRepository) -> None:
        self._repo = availability_repo

    async def execute(self, dto: UpdateAvailabilityBlockDTO) -> DoctorAvailability:
        block = await self._repo.get_block_by_id(dto.block_id)
        if block is None:
            raise NotFoundException("Bloque de disponibilidad no encontrado")

        if dto.start_time is not None:
            block.start_time = dto.start_time
        if dto.end_time is not None:
            block.end_time = dto.end_time

        block.validate()

        if await self._repo.check_overlap(
            doctor_id=block.doctor_id,
            day_of_week=block.day_of_week,
            start_time=block.start_time,
            end_time=block.end_time,
            exclude_id=block.id,
        ):
            raise ConflictException("El bloque se solapa con otro existente")

        return await self._repo.update_block(block)
