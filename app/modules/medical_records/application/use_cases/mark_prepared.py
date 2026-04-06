"""Use case: Mark a medical record as prepared."""

from app.core.exceptions import NotFoundException
from app.modules.medical_records.domain.entities.medical_record import MedicalRecord
from app.modules.medical_records.domain.repositories.medical_record_repository import (
    MedicalRecordRepository,
)


class MarkPrepared:

    def __init__(self, repo: MedicalRecordRepository) -> None:
        self._repo = repo

    async def execute(self, record_id: str, prepared_by: str) -> MedicalRecord:
        existing = await self._repo.find_by_id(record_id)
        if not existing:
            raise NotFoundException("Medical record not found.")
        return await self._repo.mark_prepared(record_id, prepared_by)
