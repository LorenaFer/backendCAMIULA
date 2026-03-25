from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional
from app.modules.appointments.domain.entities.medical_record import MedicalRecord


class MedicalRecordRepository(ABC):
    @abstractmethod
    async def get_by_appointment_id(self, appointment_id: str) -> Optional[MedicalRecord]:
        ...

    @abstractmethod
    async def upsert(self, record: MedicalRecord) -> MedicalRecord:
        """Si no existe para el appointment_id, crea. Si existe, actualiza."""
        ...

    @abstractmethod
    async def get_by_id(self, record_id: str) -> Optional[MedicalRecord]:
        ...

    @abstractmethod
    async def mark_prepared(self, record_id: str, prepared_by: str) -> None:
        ...
