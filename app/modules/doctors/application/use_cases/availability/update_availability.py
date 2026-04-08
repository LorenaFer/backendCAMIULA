"""Use case: Update availability block."""

from app.core.exceptions import NotFoundException
from app.modules.doctors.application.dtos.availability_dto import (
    UpdateAvailabilityDTO,
)
from app.modules.doctors.domain.repositories.availability_repository import (
    AvailabilityRepository,
)


class UpdateAvailability:

    def __init__(self, repo: AvailabilityRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        doctor_id: str,
        block_id: str,
        dto: UpdateAvailabilityDTO,
        updated_by: str,
    ) -> None:
        existing = await self._repo.find_by_id(doctor_id, block_id)
        if not existing:
            raise NotFoundException("Bloque de disponibilidad not found.")

        data = {
            k: v
            for k, v in {
                "day_of_week": dto.day_of_week,
                "start_time": dto.start_time,
                "end_time": dto.end_time,
                "slot_duration": dto.slot_duration,
            }.items()
            if v is not None
        }
        await self._repo.update(doctor_id, block_id, data, updated_by)
