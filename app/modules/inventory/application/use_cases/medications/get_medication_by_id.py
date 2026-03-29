"""Caso de uso: Obtener medicamento por ID."""

from typing import Optional

from app.modules.inventory.domain.entities.medication import Medication
from app.modules.inventory.domain.repositories.medication_repository import (
    MedicationRepository,
)


class GetMedicationById:

    def __init__(self, repo: MedicationRepository) -> None:
        self._repo = repo

    async def execute(self, id: str) -> Optional[Medication]:
        # find_by_id ya incluye current_stock via JOIN con batches
        return await self._repo.find_by_id(id)
