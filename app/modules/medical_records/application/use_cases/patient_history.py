"""Use case: Get patient history summary."""

from typing import List, Optional

from app.modules.medical_records.domain.repositories.medical_record_repository import (
    MedicalRecordRepository,
)


class PatientHistory:

    def __init__(self, repo: MedicalRecordRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        patient_id: str,
        limit: int = 5,
        exclude_id: Optional[str] = None,
    ) -> List[dict]:
        return await self._repo.patient_history(patient_id, limit, exclude_id)
