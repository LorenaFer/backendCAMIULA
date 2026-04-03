"""Use case: Create availability block."""

from app.modules.doctors.application.dtos.availability_dto import (
    CreateAvailabilityDTO,
)
from app.modules.doctors.domain.entities.availability import DoctorAvailability
from app.modules.doctors.domain.repositories.availability_repository import (
    AvailabilityRepository,
)


class CreateAvailability:

    def __init__(self, repo: AvailabilityRepository) -> None:
        self._repo = repo

    async def execute(
        self, dto: CreateAvailabilityDTO, created_by: str
    ) -> DoctorAvailability:
        data = {
            "fk_doctor_id": dto.fk_doctor_id,
            "day_of_week": dto.day_of_week,
            "start_time": dto.start_time,
            "end_time": dto.end_time,
            "slot_duration": dto.slot_duration,
        }
        return await self._repo.create(data, created_by)
