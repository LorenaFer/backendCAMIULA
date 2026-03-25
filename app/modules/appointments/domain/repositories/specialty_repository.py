from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Optional
from app.modules.appointments.domain.entities.specialty import Specialty


class SpecialtyRepository(ABC):
    @abstractmethod
    async def list_active(self) -> List[Specialty]:
        ...

    @abstractmethod
    async def get_by_id(self, specialty_id: str) -> Optional[Specialty]:
        ...
