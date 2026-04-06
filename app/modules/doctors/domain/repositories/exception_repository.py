"""Abstract repository interface for DoctorExceptions."""

from abc import ABC, abstractmethod
from typing import List, Optional

from app.modules.doctors.domain.entities.doctor_exception import DoctorException


class ExceptionRepository(ABC):

    @abstractmethod
    async def find_by_doctor_and_date(
        self, doctor_id: str, exception_date: Optional[str] = None
    ) -> List[DoctorException]:
        ...
