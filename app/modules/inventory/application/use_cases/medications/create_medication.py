"""Caso de uso: Crear medicamento."""

from app.core.exceptions import ConflictException
from app.modules.inventory.application.dtos.medication_dto import CreateMedicationDTO
from app.modules.inventory.domain.entities.medication import Medication
from app.modules.inventory.domain.repositories.medication_repository import (
    MedicationRepository,
)


class CreateMedication:

    def __init__(self, repo: MedicationRepository) -> None:
        self._repo = repo

    async def execute(self, dto: CreateMedicationDTO, created_by: str) -> Medication:
        existing = await self._repo.find_by_code(dto.code)
        if existing:
            raise ConflictException(
                f"Ya existe un medicamento registrado con el código '{dto.code}'."
            )

        data = {
            "code": dto.code,
            "generic_name": dto.generic_name,
            "commercial_name": dto.commercial_name,
            "pharmaceutical_form": dto.pharmaceutical_form,
            "concentration": dto.concentration,
            "unit_measure": dto.unit_measure,
            "therapeutic_class": dto.therapeutic_class,
            "controlled_substance": dto.controlled_substance,
            "requires_refrigeration": dto.requires_refrigeration,
            "medication_status": "active",
        }
        return await self._repo.create(data, created_by)
