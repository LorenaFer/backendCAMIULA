"""Use case: Find medical record by ID."""

from typing import Optional

from app.modules.medical_records.domain.entities.medical_record import MedicalRecord
from app.modules.medical_records.domain.repositories.medical_record_repository import (
    MedicalRecordRepository,
)


class FindById:

    def __init__(self, repo: MedicalRecordRepository) -> None:
        self._repo = repo

    async def execute(self, record_id: str) -> Optional[MedicalRecord]:
        return await self._repo.find_by_id(record_id)
