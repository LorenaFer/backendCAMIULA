from __future__ import annotations
from abc import ABC, abstractmethod
from datetime import date
from typing import List, Optional
from app.modules.appointments.domain.entities.availability import (
    DoctorAvailability,
    DoctorException,
)


class AvailabilityRepository(ABC):
    @abstractmethod
    async def list_by_doctor(
        self, doctor_id: str, day_of_week: Optional[int] = None
    ) -> List[DoctorAvailability]:
        ...

    @abstractmethod
    async def create_block(self, block: DoctorAvailability) -> DoctorAvailability:
        ...

    @abstractmethod
    async def get_block_by_id(self, block_id: str) -> Optional[DoctorAvailability]:
        ...

    @abstractmethod
    async def update_block(self, block: DoctorAvailability) -> DoctorAvailability:
        ...

    @abstractmethod
    async def delete_block(self, block_id: str, deleted_by: str) -> None:
        """Soft-delete del bloque."""
        ...

    @abstractmethod
    async def check_overlap(
        self, doctor_id: str, day_of_week: int, start_time, end_time, exclude_id: Optional[str] = None
    ) -> bool:
        ...

    @abstractmethod
    async def has_exception(self, doctor_id: str, check_date: date) -> bool:
        ...
