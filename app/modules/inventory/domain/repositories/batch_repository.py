"""Interfaz abstracta del repositorio de lotes."""

from abc import ABC, abstractmethod
from typing import Optional

from app.modules.inventory.domain.entities.batch import Batch


class BatchRepository(ABC):

    @abstractmethod
    async def find_all(
        self,
        medication_id: Optional[str],
        status: Optional[str],
        expiring_before: Optional[str],
        page: int,
        page_size: int,
    ) -> tuple[list[Batch], int]:
        ...

    @abstractmethod
    async def find_by_id(self, id: str) -> Optional[Batch]:
        ...

    @abstractmethod
    async def find_available_fefo(self, medication_id: str) -> list[Batch]:
        """Lotes disponibles ordenados por expiration_date ASC (FEFO) con SELECT FOR UPDATE."""
        ...

    @abstractmethod
    async def create(self, data: dict, created_by: str) -> Batch:
        ...

    @abstractmethod
    async def update_quantity(
        self, id: str, new_quantity: int, updated_by: str
    ) -> None:
        ...

    @abstractmethod
    async def update_status(
        self, id: str, new_status: str, updated_by: str
    ) -> None:
        ...
