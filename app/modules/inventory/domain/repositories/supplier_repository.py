"""Interfaz abstracta del repositorio de proveedores."""

from abc import ABC, abstractmethod
from typing import Optional

from app.modules.inventory.domain.entities.supplier import Supplier


class SupplierRepository(ABC):

    @abstractmethod
    async def find_all(
        self,
        search: Optional[str],
        status: Optional[str],
        page: int,
        page_size: int,
    ) -> tuple[list[Supplier], int]:
        ...

    @abstractmethod
    async def find_by_id(self, id: str) -> Optional[Supplier]:
        ...

    @abstractmethod
    async def find_by_rif(self, rif: str) -> Optional[Supplier]:
        ...

    @abstractmethod
    async def find_options(self) -> list[Supplier]:
        """Simplified list for dropdowns: id, name, rif."""
        ...

    @abstractmethod
    async def create(self, data: dict, created_by: str) -> Supplier:
        ...

    @abstractmethod
    async def update(self, id: str, data: dict, updated_by: str) -> Supplier:
        ...

    @abstractmethod
    async def soft_delete(self, id: str, deleted_by: str) -> None:
        ...
