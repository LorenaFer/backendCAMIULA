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
        """Returns (entity, was_created: bool).

        Delegates to a single atomic INSERT ... ON CONFLICT in the repository so
        that concurrent autosave requests from the clinical wizard cannot race
        and produce duplicate records. This is what makes the autosave loop
        safe under flaky connectivity.
        """
        data = {
            "fk_appointment_id": dto.fk_appointment_id,
            "fk_patient_id": dto.fk_patient_id,
            "fk_doctor_id": dto.fk_doctor_id,
            "evaluation": dto.evaluation,
            "schema_id": dto.schema_id,
            "schema_version": dto.schema_version,
        }
        return await self._repo.upsert_by_appointment(data, user_id=user_id)
