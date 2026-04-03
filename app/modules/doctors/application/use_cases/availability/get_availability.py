"""Use case: Get doctor availability blocks."""

from typing import List, Optional

from app.modules.doctors.domain.entities.availability import DoctorAvailability
from app.modules.doctors.domain.repositories.availability_repository import (
    AvailabilityRepository,
)


class GetAvailability:

    def __init__(self, repo: AvailabilityRepository) -> None:
        self._repo = repo

    async def execute(
        self, doctor_id: str, day_of_week: Optional[int] = None
    ) -> List[DoctorAvailability]:
        return await self._repo.find_by_doctor(doctor_id, day_of_week)
