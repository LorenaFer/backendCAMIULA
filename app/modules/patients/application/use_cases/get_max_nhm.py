"""Use case: get the highest NHM registered."""

from app.modules.patients.domain.repositories.patient_repository import (
    PatientRepository,
)


class GetMaxNhm:
    def __init__(self, repo: PatientRepository) -> None:
        self._repo = repo

    async def execute(self) -> int:
        return await self._repo.get_max_nhm()
