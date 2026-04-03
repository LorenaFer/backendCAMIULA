"""Use case: Update specialty."""

from app.core.exceptions import NotFoundException
from app.modules.doctors.application.dtos.specialty_dto import UpdateSpecialtyDTO
from app.modules.doctors.domain.entities.specialty import Specialty
from app.modules.doctors.domain.repositories.specialty_repository import (
    SpecialtyRepository,
)


class UpdateSpecialty:

    def __init__(self, repo: SpecialtyRepository) -> None:
        self._repo = repo

    async def execute(
        self, id: str, dto: UpdateSpecialtyDTO, updated_by: str
    ) -> Specialty:
        existing = await self._repo.find_by_id(id)
        if not existing:
            raise NotFoundException("Especialidad no encontrada.")

        data = {k: v for k, v in {"name": dto.name}.items() if v is not None}
        return await self._repo.update(id, data, updated_by)
