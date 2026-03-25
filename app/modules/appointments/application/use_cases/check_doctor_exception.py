from datetime import date
from app.modules.appointments.domain.repositories.availability_repository import AvailabilityRepository


class CheckDoctorExceptionUseCase:
    def __init__(self, availability_repo: AvailabilityRepository) -> None:
        self._repo = availability_repo

    async def execute(self, doctor_id: str, check_date: date) -> bool:
        return await self._repo.has_exception(doctor_id, check_date)
