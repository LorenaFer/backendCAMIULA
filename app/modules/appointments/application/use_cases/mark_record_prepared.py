from app.core.exceptions import NotFoundException
from app.modules.appointments.domain.repositories.medical_record_repository import MedicalRecordRepository


class MarkRecordPreparedUseCase:
    def __init__(self, medical_record_repo: MedicalRecordRepository) -> None:
        self._repo = medical_record_repo

    async def execute(self, record_id: str, prepared_by: str) -> None:
        record = await self._repo.get_by_id(record_id)
        if record is None:
            raise NotFoundException("Historia médica no encontrada")
        await self._repo.mark_prepared(record_id, prepared_by)
