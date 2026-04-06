"""Abstract repository interface for Doctors."""

from abc import ABC, abstractmethod
from typing import List, Optional

from app.modules.doctors.domain.entities.doctor import Doctor


class DoctorRepository(ABC):

    @abstractmethod
    async def find_all_active(self) -> List[Doctor]:
        ...

    @abstractmethod
    async def find_options(self) -> List[Doctor]:
        ...

    @abstractmethod
    async def find_by_id(self, id: str) -> Optional[Doctor]:
        ...
