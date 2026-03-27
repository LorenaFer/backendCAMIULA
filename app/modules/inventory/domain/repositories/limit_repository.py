"""Interfaz abstracta del repositorio de límites y excepciones de despacho."""

from abc import ABC, abstractmethod
from typing import Optional

from app.modules.inventory.domain.entities.dispatch_limit import (
    DispatchException,
    DispatchLimit,
)


class LimitRepository(ABC):

    @abstractmethod
    async def find_all_limits(
        self,
        medication_id: Optional[str],
        page: int,
        page_size: int,
    ) -> tuple[list[DispatchLimit], int]:
        ...

    @abstractmethod
    async def find_limit_by_id(self, id: str) -> Optional[DispatchLimit]:
        ...

    @abstractmethod
    async def find_active_limit(
        self, fk_medication_id: str, applies_to: str
    ) -> Optional[DispatchLimit]:
        """Encuentra el límite activo para un medicamento y tipo de beneficiario."""
        ...

    @abstractmethod
    async def create_limit(self, data: dict, created_by: str) -> DispatchLimit:
        ...

    @abstractmethod
    async def update_limit(
        self, id: str, data: dict, updated_by: str
    ) -> DispatchLimit:
        ...

    @abstractmethod
    async def find_all_exceptions(
        self,
        patient_id: Optional[str],
        medication_id: Optional[str],
        page: int,
        page_size: int,
    ) -> tuple[list[DispatchException], int]:
        ...

    @abstractmethod
    async def find_active_exception(
        self,
        fk_patient_id: str,
        fk_medication_id: str,
        reference_date: str,
    ) -> Optional[DispatchException]:
        """Encuentra excepción vigente (valid_from <= date <= valid_until)."""
        ...

    @abstractmethod
    async def create_exception(
        self, data: dict, created_by: str
    ) -> DispatchException:
        ...
