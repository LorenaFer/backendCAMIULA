"""Caso de uso: Actualizar medicamento."""

from app.core.exceptions import NotFoundException
from app.modules.inventory.application.dtos.medication_dto import UpdateMedicationDTO
from app.modules.inventory.domain.entities.medication import Medication
from app.modules.inventory.domain.repositories.medication_repository import (
    MedicationRepository,
)


class UpdateMedication:

    def __init__(self, repo: MedicationRepository) -> None:
        self._repo = repo

    async def execute(
        self, id: str, dto: UpdateMedicationDTO, updated_by: str
    ) -> Medication:
        existing = await self._repo.find_by_id(id)
        if not existing:
            raise NotFoundException("Medicamento no encontrado.")

        data = {
            k: v
            for k, v in {
                "generic_name": dto.generic_name,
                "commercial_name": dto.commercial_name,
                "pharmaceutical_form": dto.pharmaceutical_form,
                "concentration": dto.concentration,
                "unit_measure": dto.unit_measure,
                "therapeutic_class": dto.therapeutic_class,
                "fk_category_id": dto.fk_category_id,
                "controlled_substance": dto.controlled_substance,
                "requires_refrigeration": dto.requires_refrigeration,
                "medication_status": dto.medication_status,
            }.items()
            if v is not None
        }
        return await self._repo.update(id, data, updated_by)
