"""Use case: List all specialties."""

from typing import List

from app.modules.doctors.domain.entities.specialty import Specialty
from app.modules.doctors.domain.repositories.specialty_repository import (
    SpecialtyRepository,
)


class GetSpecialties:

    def __init__(self, repo: SpecialtyRepository) -> None:
        self._repo = repo

    async def execute(self) -> List[Specialty]:
        return await self._repo.find_all()
