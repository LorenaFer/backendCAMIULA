"""Abstract repository interface for DoctorAvailability."""

from abc import ABC, abstractmethod
from typing import List, Optional

from app.modules.doctors.domain.entities.availability import DoctorAvailability


class AvailabilityRepository(ABC):

    @abstractmethod
    async def find_by_doctor(
        self, doctor_id: str, day_of_week: Optional[int] = None
    ) -> List[DoctorAvailability]:
        ...

    @abstractmethod
    async def find_by_id(
        self, doctor_id: str, block_id: str
    ) -> Optional[DoctorAvailability]:
        ...

    @abstractmethod
    async def create(self, data: dict, created_by: str) -> DoctorAvailability:
        ...

    @abstractmethod
    async def update(
        self, doctor_id: str, block_id: str, data: dict, updated_by: str
    ) -> None:
        ...

    @abstractmethod
    async def soft_delete(
        self, doctor_id: str, block_id: str, deleted_by: str
    ) -> None:
        ...
