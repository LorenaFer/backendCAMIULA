"""Interfaz abstracta del repositorio de despachos."""

from abc import ABC, abstractmethod
from typing import Optional

from app.modules.inventory.domain.entities.dispatch import Dispatch


class DispatchRepository(ABC):

    @abstractmethod
    async def find_by_id(self, id: str) -> Optional[Dispatch]:
        ...

    @abstractmethod
    async def find_by_prescription(self, fk_prescription_id: str) -> list[Dispatch]:
        ...

    @abstractmethod
    async def find_by_patient(
        self,
        fk_patient_id: str,
        prescription_number: Optional[str],
        status: Optional[str],
        date_from: Optional[str],
        date_to: Optional[str],
        page: int,
        page_size: int,
    ) -> tuple[list[Dispatch], int]:
        ...

    @abstractmethod
    async def get_monthly_consumption(
        self, fk_patient_id: str, fk_medication_id: str, month: str, year: int
    ) -> int:
        """Total despachado a un paciente de un medicamento en un mes dado."""
        ...

    @abstractmethod
    async def create(self, data: dict, created_by: str) -> Dispatch:
        ...

    @abstractmethod
    async def update_status(
        self, id: str, new_status: str, updated_by: str
    ) -> None:
        ...
