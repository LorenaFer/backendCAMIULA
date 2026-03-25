from typing import Optional

from app.modules.patients.domain.entities.patient import Patient
from app.modules.patients.domain.repositories.patient_repository import PatientRepository


class SearchPatientByNhmUseCase:
    """Busca paciente por NHM. Retorna datos reducidos (público).

    Complejidad: O(log n) — lookup por índice único.
    """

    def __init__(self, patient_repo: PatientRepository) -> None:
        self._repo = patient_repo

    async def execute(self, nhm: int) -> Optional[Patient]:
        return await self._repo.get_by_nhm(nhm)


class SearchPatientByCedulaUseCase:
    """Busca paciente por cédula. Retorna datos reducidos (público).

    Complejidad: O(log n) — lookup por índice único.
    """

    def __init__(self, patient_repo: PatientRepository) -> None:
        self._repo = patient_repo

    async def execute(self, cedula: str) -> Optional[Patient]:
        return await self._repo.get_by_cedula(cedula)
