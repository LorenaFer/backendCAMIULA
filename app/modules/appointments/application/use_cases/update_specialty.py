from __future__ import annotations
from typing import Optional

from app.core.exceptions import AppException
from app.modules.appointments.domain.entities.specialty import Specialty
from app.modules.appointments.domain.repositories.specialty_repository import (
    SpecialtyRepository,
)


class UpdateSpecialtyUseCase:
    """Actualiza el nombre de una especialidad. O(log n) por PK lookup."""

    def __init__(self, specialty_repo: SpecialtyRepository) -> None:
        self._repo = specialty_repo

    async def execute(
        self, specialty_id: str, name: str, updated_by: Optional[str] = None
    ) -> Specialty:
        specialty = await self._repo.get_by_id(specialty_id)
        if specialty is None:
            raise AppException("Especialidad no encontrada", status_code=404)

        # Verificar que no exista otra especialidad con el mismo nombre
        duplicate = await self._repo.get_by_name(name)
        if duplicate is not None and duplicate.id != specialty_id:
            raise AppException(
                f"Ya existe una especialidad con el nombre '{name}'",
                status_code=409,
            )

        specialty.name = name
        return await self._repo.update(specialty, updated_by=updated_by)
