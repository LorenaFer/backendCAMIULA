"""Abstract repository interface for appointments."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

from app.modules.appointments.domain.entities.appointment import Appointment


class AppointmentRepository(ABC):

    @abstractmethod
    async def create(self, data: dict, created_by: str) -> Appointment:
        ...

    @abstractmethod
    async def find_by_id(self, appointment_id: str) -> Optional[Appointment]:
        ...

    @abstractmethod
    async def find_by_client_token(self, client_token: str) -> Optional[Appointment]:
        """Lookup an existing appointment by the client-generated idempotency token.

        Returns the appointment if a previous request with the same token already
        succeeded; None otherwise. Used to make POST /appointments idempotent.
        """
        ...

    @abstractmethod
    async def find_all(
        self,
        page: int,
        page_size: int,
        date_str: Optional[str] = None,
        doctor_id: Optional[str] = None,
        specialty_id: Optional[str] = None,
        status_filter: Optional[str] = None,
        q: Optional[str] = None,
    ) -> Tuple[List[Appointment], int]:
        """Paginated list with patient+doctor data."""
        ...

    @abstractmethod
    async def find_by_doctor_and_month(
        self,
        doctor_id: str,
        year: int,
        month: int,
        exclude_cancelled: bool = True,
    ) -> List[Appointment]:
        ...

    @abstractmethod
    async def find_by_doctor_and_date(
        self,
        doctor_id: str,
        date_str: str,
        exclude_cancelled: bool = True,
    ) -> List[Appointment]:
        ...

    @abstractmethod
    async def check_double_booking(
        self, doctor_id: str, date_str: str, start_time: str
    ) -> bool:
        """Returns True if a non-cancelled appointment exists for the slot."""
        ...

    @abstractmethod
    async def update_status(
        self,
        appointment_id: str,
        new_status: str,
        updated_by: str,
    ) -> Appointment:
        ...

    @abstractmethod
    async def get_stats(
        self,
        date_str: Optional[str] = None,
        doctor_id: Optional[str] = None,
        specialty_id: Optional[str] = None,
        status_filter: Optional[str] = None,
    ) -> Dict[str, Any]:
        ...

    @abstractmethod
    async def find_non_cancelled_by_doctor_and_date(
        self, doctor_id: str, date_str: str
    ) -> List[Appointment]:
        """Existing non-cancelled appointments for slot computation."""
        ...
