"""Use case: search patient by NHM or dni (public version)."""

from typing import Optional

from app.modules.patients.domain.entities.patient import Patient
from app.modules.patients.domain.repositories.patient_repository import (
    PatientRepository,
)


class SearchPatientByNhm:
    def __init__(self, repo: PatientRepository) -> None:
        self._repo = repo

    async def execute(self, nhm: int) -> Optional[Patient]:
        return await self._repo.find_by_nhm(nhm)


class SearchPatientByDni:
    def __init__(self, repo: PatientRepository) -> None:
        self._repo = repo

    async def execute(self, dni: str) -> Optional[Patient]:
        return await self._repo.find_by_dni(dni)
