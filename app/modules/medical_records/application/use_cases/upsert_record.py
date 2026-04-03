"""Use case: Upsert medical record (create or update by fk_appointment_id)."""

from app.modules.medical_records.application.dtos.medical_record_dto import (
    UpsertMedicalRecordDTO,
)
from app.modules.medical_records.domain.entities.medical_record import MedicalRecord
from app.modules.medical_records.domain.repositories.medical_record_repository import (
    MedicalRecordRepository,
)


class UpsertRecord:

    def __init__(self, repo: MedicalRecordRepository) -> None:
        self._repo = repo

    async def execute(self, dto: UpsertMedicalRecordDTO, user_id: str) -> tuple:
        """Returns (entity, was_created: bool)."""
        existing = await self._repo.find_by_appointment_id(dto.fk_appointment_id)

        data = {
            "fk_appointment_id": dto.fk_appointment_id,
            "fk_patient_id": dto.fk_patient_id,
            "fk_doctor_id": dto.fk_doctor_id,
            "evaluation": dto.evaluation,
            "schema_id": dto.schema_id,
            "schema_version": dto.schema_version,
        }

        if existing:
            # Update -- remove fk_appointment_id from update payload (it's the key)
            update_data = {k: v for k, v in data.items() if k != "fk_appointment_id"}
            record = await self._repo.update(existing.id, update_data, updated_by=user_id)
            return record, False
        else:
            record = await self._repo.create(data, created_by=user_id)
            return record, True
