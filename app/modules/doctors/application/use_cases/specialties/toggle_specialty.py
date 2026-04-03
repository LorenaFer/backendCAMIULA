"""Use case: Toggle specialty status between A and I."""

from app.core.exceptions import NotFoundException
from app.modules.doctors.domain.entities.specialty import Specialty
from app.modules.doctors.domain.repositories.specialty_repository import (
    SpecialtyRepository,
)


class ToggleSpecialty:

    def __init__(self, repo: SpecialtyRepository) -> None:
        self._repo = repo

    async def execute(self, id: str, updated_by: str) -> Specialty:
        existing = await self._repo.find_by_id(id)
        if not existing:
            raise NotFoundException("Especialidad no encontrada.")
        return await self._repo.toggle_status(id, updated_by)
