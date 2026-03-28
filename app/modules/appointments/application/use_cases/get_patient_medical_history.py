from __future__ import annotations
from typing import List, Optional

from app.modules.appointments.domain.entities.medical_record import MedicalRecord
from app.modules.appointments.domain.repositories.medical_record_repository import (
    MedicalRecordRepository,
)


class GetPatientMedicalHistoryUseCase:
    """Historial médico previo de un paciente. O(log n + k)."""

    def __init__(self, medical_record_repo: MedicalRecordRepository) -> None:
        self._repo = medical_record_repo

    async def execute(
        self,
        patient_id: str,
        limit: int = 5,
        exclude_appointment_id: Optional[str] = None,
    ) -> List[MedicalRecord]:
        return await self._repo.get_patient_history(
            patient_id=patient_id,
            limit=limit,
            exclude_appointment_id=exclude_appointment_id,
        )
