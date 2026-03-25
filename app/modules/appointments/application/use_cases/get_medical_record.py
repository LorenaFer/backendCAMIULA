from typing import Optional
from app.modules.appointments.domain.entities.medical_record import MedicalRecord
from app.modules.appointments.domain.repositories.medical_record_repository import MedicalRecordRepository


class GetMedicalRecordUseCase:
    def __init__(self, medical_record_repo: MedicalRecordRepository) -> None:
        self._repo = medical_record_repo

    async def execute(self, appointment_id: str) -> Optional[MedicalRecord]:
        return await self._repo.get_by_appointment_id(appointment_id)
