"""Caso de uso: búsqueda de paciente por cédula o NHM."""

from app.core.exceptions import AppException, NotFoundException
from app.modules.patients.application.dtos.patient_dto import SearchPatientDTO
from app.modules.patients.domain.entities.patient import Patient
from app.modules.patients.domain.repositories.patient_repository import PatientRepository


class SearchPatient:

    def __init__(self, repo: PatientRepository) -> None:
        self._repo = repo

    async def execute(self, dto: SearchPatientDTO) -> Patient:
        has_cedula = bool(dto.cedula)
        has_nhm = dto.nhm is not None

        if has_cedula == has_nhm:
            raise AppException(
                "Debe enviar cedula o nhm, pero no ambos",
                status_code=400,
            )

        patient = (
            await self._repo.find_by_cedula(dto.cedula.strip())
            if has_cedula
            else await self._repo.find_by_nhm(dto.nhm)
        )
        if not patient:
            raise NotFoundException("Paciente no encontrado")
        return patient
