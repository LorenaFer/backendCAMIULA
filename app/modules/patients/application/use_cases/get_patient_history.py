"""Caso de uso: historial resumido del paciente."""

from app.core.exceptions import NotFoundException
from app.modules.patients.application.dtos.patient_dto import GetPatientHistoryDTO
from app.modules.patients.domain.entities.patient import PatientHistoryEntry
from app.modules.patients.domain.repositories.patient_repository import PatientRepository


class GetPatientHistory:

    def __init__(self, repo: PatientRepository) -> None:
        self._repo = repo

    async def execute(self, dto: GetPatientHistoryDTO) -> list[PatientHistoryEntry]:
        patient = await self._repo.find_by_id(dto.patient_id)
        if not patient:
            raise NotFoundException("Paciente no encontrado")

        return await self._repo.list_history(
            patient_id=dto.patient_id,
            limit=dto.limit,
            exclude_appointment_id=dto.exclude_appointment_id,
        )
