"""Interfaz abstracta del repositorio de medicamentos."""

from abc import ABC, abstractmethod
from typing import Optional

from app.modules.inventory.domain.entities.medication import Medication


class MedicationRepository(ABC):

    @abstractmethod
    async def find_all(
        self,
        search: Optional[str],
        status: Optional[str],
        therapeutic_class: Optional[str],
        page: int,
        page_size: int,
        category_id: Optional[str] = None,
    ) -> tuple[list[Medication], int]:
        """Retorna (items, total) para paginación."""
        ...

    @abstractmethod
    async def find_by_id(self, id: str) -> Optional[Medication]:
        ...

    @abstractmethod
    async def find_by_code(self, code: str) -> Optional[Medication]:
        ...

    @abstractmethod
    async def find_options(self) -> list[Medication]:
        """Lista simplificada para selects: id, code, generic_name, pharmaceutical_form, unit_measure, current_stock."""
        ...

    @abstractmethod
    async def create(self, data: dict, created_by: str) -> Medication:
        ...

    @abstractmethod
    async def update(self, id: str, data: dict, updated_by: str) -> Medication:
        ...

    @abstractmethod
    async def soft_delete(self, id: str, deleted_by: str) -> None:
        ...

    @abstractmethod
    async def get_current_stock(self, medication_id: str) -> int:
        """Suma de quantity_available en lotes activos y disponibles."""
        ...
