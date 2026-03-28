from __future__ import annotations
from typing import Optional

from app.core.exceptions import AppException
from app.modules.appointments.domain.entities.specialty import Specialty
from app.modules.appointments.domain.repositories.specialty_repository import (
    SpecialtyRepository,
)


class ToggleSpecialtyUseCase:
    """Alterna el estado activo/inactivo de una especialidad. O(log n)."""

    def __init__(self, specialty_repo: SpecialtyRepository) -> None:
        self._repo = specialty_repo

    async def execute(
        self, specialty_id: str, updated_by: Optional[str] = None
    ) -> Specialty:
        specialty = await self._repo.get_by_id(specialty_id)
        if specialty is None:
            raise AppException("Especialidad no encontrada", status_code=404)

        return await self._repo.toggle(specialty_id, updated_by=updated_by)
