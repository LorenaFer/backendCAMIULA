from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Optional
from app.modules.appointments.domain.entities.doctor import Doctor


class DoctorRepository(ABC):
    @abstractmethod
    async def list_active(self) -> List[Doctor]:
        ...

    @abstractmethod
    async def get_by_id(self, doctor_id: str) -> Optional[Doctor]:
        ...

    @abstractmethod
    async def get_by_user_id(self, user_id: str) -> Optional[Doctor]:
        ...

    @abstractmethod
    async def list_options(self) -> List[Doctor]:
        """Doctores para selectores, incluye días de trabajo."""
        ...
