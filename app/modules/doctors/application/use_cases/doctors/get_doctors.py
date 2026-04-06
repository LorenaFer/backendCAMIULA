"""Use case: List active doctors."""

from typing import List

from app.modules.doctors.domain.entities.doctor import Doctor
from app.modules.doctors.domain.repositories.doctor_repository import (
    DoctorRepository,
)


class GetDoctors:

    def __init__(self, repo: DoctorRepository) -> None:
        self._repo = repo

    async def execute(self) -> List[Doctor]:
        return await self._repo.find_all_active()
