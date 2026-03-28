from __future__ import annotations
from typing import Optional

from app.core.exceptions import AppException
from app.modules.appointments.domain.entities.specialty import Specialty
from app.modules.appointments.domain.repositories.specialty_repository import (
    SpecialtyRepository,
)


class CreateSpecialtyUseCase:
    """Crea una nueva especialidad. O(1) escritura + O(n) check unicidad."""

    def __init__(self, specialty_repo: SpecialtyRepository) -> None:
        self._repo = specialty_repo

    async def execute(self, name: str, created_by: Optional[str] = None) -> Specialty:
        existing = await self._repo.get_by_name(name)
        if existing is not None:
            raise AppException(
                f"Ya existe una especialidad con el nombre '{name}'",
                status_code=409,
            )
        specialty = Specialty(name=name)
        return await self._repo.create(specialty, created_by=created_by)
