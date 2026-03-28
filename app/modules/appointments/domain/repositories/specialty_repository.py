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

    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[Specialty]:
        ...

    @abstractmethod
    async def create(self, specialty: Specialty, created_by: Optional[str] = None) -> Specialty:
        ...

    @abstractmethod
    async def update(self, specialty: Specialty, updated_by: Optional[str] = None) -> Specialty:
        ...

    @abstractmethod
    async def toggle(self, specialty_id: str, updated_by: Optional[str] = None) -> Specialty:
        ...
