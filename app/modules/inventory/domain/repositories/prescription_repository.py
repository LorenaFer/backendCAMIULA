"""Interfaz abstracta del repositorio de recetas médicas."""

from abc import ABC, abstractmethod
from typing import Optional

from app.modules.inventory.domain.entities.prescription import Prescription


class PrescriptionRepository(ABC):

    @abstractmethod
    async def find_by_id(self, id: str) -> Optional[Prescription]:
        ...

    @abstractmethod
    async def find_by_appointment(
        self, fk_appointment_id: str
    ) -> Optional[Prescription]:
        ...

    @abstractmethod
    async def find_by_patient(
        self, fk_patient_id: str, page: int, page_size: int
    ) -> tuple[list[Prescription], int]:
        ...

    @abstractmethod
    async def find_by_number(self, prescription_number: str) -> Optional[Prescription]:
        ...

    @abstractmethod
    async def create(self, data: dict, created_by: str) -> Prescription:
        ...

    @abstractmethod
    async def update_status(
        self, id: str, new_status: str, updated_by: str
    ) -> None:
        ...

    @abstractmethod
    async def get_next_number(self) -> str:
        """Genera el número correlativo: PRX-YYYY-NNNN."""
        ...
