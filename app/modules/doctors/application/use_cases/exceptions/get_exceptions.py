"""Use case: Get doctor exceptions."""

from typing import List, Optional

from app.modules.doctors.domain.entities.doctor_exception import DoctorException
from app.modules.doctors.domain.repositories.exception_repository import (
    ExceptionRepository,
)


class GetExceptions:

    def __init__(self, repo: ExceptionRepository) -> None:
        self._repo = repo

    async def execute(
        self, doctor_id: str, exception_date: Optional[str] = None
    ) -> List[DoctorException]:
        return await self._repo.find_by_doctor_and_date(doctor_id, exception_date)
