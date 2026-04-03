"""Abstract repository interface for Medical Records."""

from abc import ABC, abstractmethod
from typing import Any, List, Optional

from app.modules.medical_records.domain.entities.medical_record import MedicalRecord


class MedicalRecordRepository(ABC):

    @abstractmethod
    async def find_by_appointment_id(self, appointment_id: str) -> Optional[MedicalRecord]:
        ...

    @abstractmethod
    async def find_by_id(self, record_id: str) -> Optional[MedicalRecord]:
        ...

    @abstractmethod
    async def create(self, data: dict, created_by: str) -> MedicalRecord:
        ...

    @abstractmethod
    async def update(self, record_id: str, data: dict, updated_by: str) -> MedicalRecord:
        ...

    @abstractmethod
    async def mark_prepared(self, record_id: str, prepared_by: str) -> MedicalRecord:
        ...

    @abstractmethod
    async def patient_history(
        self,
        patient_id: str,
        limit: int,
        exclude_id: Optional[str],
    ) -> List[dict]:
        """Return patient history summary with cross-module joins."""
        ...
