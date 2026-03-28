from app.modules.appointments.application.dtos.medical_record_dto import UpsertMedicalRecordDTO
from app.modules.appointments.domain.entities.medical_record import MedicalRecord
from app.modules.appointments.domain.repositories.medical_record_repository import MedicalRecordRepository


class UpsertMedicalRecordUseCase:
    """Crea o actualiza historia médica (upsert por appointment_id)."""

    def __init__(self, medical_record_repo: MedicalRecordRepository) -> None:
        self._repo = medical_record_repo

    async def execute(self, dto: UpsertMedicalRecordDTO) -> MedicalRecord:
        record = MedicalRecord(
            appointment_id=dto.appointment_id,
            patient_id=dto.patient_id,
            doctor_id=dto.doctor_id,
            schema_id=dto.schema_id,
            schema_version=dto.schema_version,
            evaluation=dto.evaluation,
        )
        return await self._repo.upsert(record)
