from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional, Tuple
from app.modules.patients.domain.entities.patient import Patient


class PatientRepository(ABC):

    @abstractmethod
    async def create(self, patient: Patient) -> Patient:
        ...

    @abstractmethod
    async def get_by_id(self, patient_id: str) -> Optional[Patient]:
        ...

    @abstractmethod
    async def get_by_cedula(self, cedula: str) -> Optional[Patient]:
        ...

    @abstractmethod
    async def get_by_nhm(self, nhm: int) -> Optional[Patient]:
        ...

    @abstractmethod
    async def get_max_nhm(self) -> int:
        ...

    @abstractmethod
    async def next_nhm(self) -> int:
        """Obtiene el siguiente NHM usando la secuencia PostgreSQL."""
        ...

    @abstractmethod
    async def exists_by_cedula(self, cedula: str) -> bool:
        ...
