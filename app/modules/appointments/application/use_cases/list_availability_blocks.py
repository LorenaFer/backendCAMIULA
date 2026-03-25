from typing import List, Optional
from app.modules.appointments.domain.entities.availability import DoctorAvailability
from app.modules.appointments.domain.repositories.availability_repository import AvailabilityRepository


class ListAvailabilityBlocksUseCase:
    def __init__(self, availability_repo: AvailabilityRepository) -> None:
        self._repo = availability_repo

    async def execute(
        self, doctor_id: str, day_of_week: Optional[int] = None
    ) -> List[DoctorAvailability]:
        return await self._repo.list_by_doctor(doctor_id, day_of_week)
