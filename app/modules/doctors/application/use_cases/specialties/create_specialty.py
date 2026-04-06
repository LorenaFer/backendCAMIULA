"""Use case: Create specialty."""

from app.core.exceptions import ConflictException
from app.modules.doctors.application.dtos.specialty_dto import CreateSpecialtyDTO
from app.modules.doctors.domain.entities.specialty import Specialty
from app.modules.doctors.domain.repositories.specialty_repository import (
    SpecialtyRepository,
)


class CreateSpecialty:

    def __init__(self, repo: SpecialtyRepository) -> None:
        self._repo = repo

    async def execute(self, dto: CreateSpecialtyDTO, created_by: str) -> Specialty:
        existing = await self._repo.find_by_name(dto.name)
        if existing:
            raise ConflictException(
                f"A specialty with the name '{dto.name}'."
            )
        data = {"name": dto.name}
        return await self._repo.create(data, created_by)
