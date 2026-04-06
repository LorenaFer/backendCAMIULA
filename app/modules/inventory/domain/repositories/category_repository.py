"""Abstract interface for the Medication Category repository."""

from abc import ABC, abstractmethod
from typing import Optional

from app.modules.inventory.domain.entities.category import MedicationCategory


class CategoryRepository(ABC):

    @abstractmethod
    async def find_all(
        self, search: Optional[str], page: int, page_size: int
    ) -> tuple[list[MedicationCategory], int]:
        ...

    @abstractmethod
    async def find_by_id(self, id: str) -> Optional[MedicationCategory]:
        ...

    @abstractmethod
    async def find_by_name(self, name: str) -> Optional[MedicationCategory]:
        ...

    @abstractmethod
    async def create(self, data: dict, created_by: str) -> MedicationCategory:
        ...

    @abstractmethod
    async def update(self, id: str, data: dict, updated_by: str) -> Optional[MedicationCategory]:
        ...

    @abstractmethod
    async def soft_delete(self, id: str, deleted_by: str) -> bool:
        ...
