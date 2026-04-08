"""Caso de uso: List medications con filtros y paginación."""

from typing import Optional

from app.modules.inventory.domain.entities.medication import Medication
from app.modules.inventory.domain.repositories.medication_repository import (
    MedicationRepository,
)


class GetMedications:

    def __init__(self, repo: MedicationRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        search: Optional[str],
        status: Optional[str],
        therapeutic_class: Optional[str],
        page: int,
        page_size: int,
        category_id: Optional[str] = None,
    ) -> tuple[list[Medication], int]:
        return await self._repo.find_all(
            search=search,
            status=status,
            therapeutic_class=therapeutic_class,
            category_id=category_id,
            page=page,
            page_size=page_size,
        )
