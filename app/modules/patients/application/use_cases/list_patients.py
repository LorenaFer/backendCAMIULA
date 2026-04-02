"""Use case: list patients with pagination."""

from app.modules.patients.domain.entities.patient import Patient
from app.modules.patients.domain.repositories.patient_repository import (
    PatientRepository,
)


class ListPatients:
    def __init__(self, repo: PatientRepository) -> None:
        self._repo = repo

    async def execute(
        self, page: int = 1, page_size: int = 20
    ) -> tuple[list[Patient], int]:
        return await self._repo.find_all(page, page_size)
