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
        medication = await self._repo.find_by_id(id)
        if medication:
            medication.current_stock = await self._repo.get_current_stock(id)
        return medication
