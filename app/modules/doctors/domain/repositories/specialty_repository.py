"""Abstract repository interface for Specialties."""

from abc import ABC, abstractmethod
from typing import Optional

from app.modules.doctors.domain.entities.specialty import Specialty


class SpecialtyRepository(ABC):

    @abstractmethod
    async def find_all(self) -> list:
        ...

    @abstractmethod
    async def find_by_id(self, id: str) -> Optional[Specialty]:
        ...

    @abstractmethod
    async def find_by_name(self, name: str) -> Optional[Specialty]:
        ...

    @abstractmethod
    async def create(self, data: dict, created_by: str) -> Specialty:
        ...

    @abstractmethod
    async def update(self, id: str, data: dict, updated_by: str) -> Specialty:
        ...

    @abstractmethod
    async def toggle_status(self, id: str, updated_by: str) -> Specialty:
        ...
