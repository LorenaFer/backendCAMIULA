"""Abstract repository interface for patients."""

from abc import ABC, abstractmethod
from typing import Optional

from app.modules.patients.domain.entities.patient import Patient


class PatientRepository(ABC):

    @abstractmethod
    async def find_all(
        self, page: int, page_size: int, search: Optional[str] = None
    ) -> tuple[list[Patient], int]:
        """Returns (items, total) paginated by last_name, with optional text search."""
        ...

    @abstractmethod
    async def find_by_nhm(self, nhm: int) -> Optional[Patient]:
        ...

    @abstractmethod
    async def find_by_cedula(self, cedula: str) -> Optional[Patient]:
        ...

    @abstractmethod
    async def get_max_nhm(self) -> int:
        """Returns the highest NHM registered, or 0 if no patients."""
        ...

    @abstractmethod
    async def create(self, data: dict, created_by: str) -> Patient:
        ...

    @abstractmethod
    async def get_next_nhm(self) -> int:
        """Gets next NHM with SELECT FOR UPDATE to prevent race conditions."""
        ...
