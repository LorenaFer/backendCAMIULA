"""Contrato abstracto del repositorio de pacientes."""

from abc import ABC, abstractmethod
from typing import Optional

from app.modules.patients.domain.entities.patient import Patient, PatientHistoryEntry


class PatientRepository(ABC):

    @abstractmethod
    async def find_by_cedula(self, cedula: str) -> Optional[Patient]:
        ...

    @abstractmethod
    async def find_by_nhm(self, nhm: int) -> Optional[Patient]:
        ...

    @abstractmethod
    async def find_by_id(self, patient_id: str) -> Optional[Patient]:
        ...

    @abstractmethod
    async def get_next_nhm(self) -> int:
        ...

    @abstractmethod
    async def create(self, data: dict, created_by: str) -> Patient:
        ...

    @abstractmethod
    async def list_history(
        self,
        patient_id: str,
        limit: int,
        exclude_appointment_id: Optional[str],
    ) -> list[PatientHistoryEntry]:
        ...
