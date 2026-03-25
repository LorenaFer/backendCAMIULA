from typing import List
from app.modules.appointments.domain.entities.specialty import Specialty
from app.modules.appointments.domain.repositories.specialty_repository import SpecialtyRepository


class ListSpecialtiesUseCase:
    """Lista especialidades activas. O(n) — tabla pequeña, sin paginación."""

    def __init__(self, specialty_repo: SpecialtyRepository) -> None:
        self._repo = specialty_repo

    async def execute(self) -> List[Specialty]:
        return await self._repo.list_active()
