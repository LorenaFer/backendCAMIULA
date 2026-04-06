"""Caso de uso: Delete medication (soft-delete)."""

from app.core.exceptions import NotFoundException
from app.modules.inventory.domain.repositories.medication_repository import (
    MedicationRepository,
)


class SoftDeleteMedication:

    def __init__(self, repo: MedicationRepository) -> None:
        self._repo = repo

    async def execute(self, id: str, deleted_by: str) -> None:
        existing = await self._repo.find_by_id(id)
        if not existing:
            raise NotFoundException("Medication not found.")
        await self._repo.soft_delete(id, deleted_by)
