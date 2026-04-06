"""Abstract interface for reading doctor availability data.

Used by the appointments module to compute available slots and dates
without importing infrastructure models directly.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, time
from typing import List, Optional, Set


@dataclass
class AvailabilityBlock:
    """A single time block when a doctor is available."""
    id: str
    fk_doctor_id: str
    day_of_week: int          # 1=Mon ... 7=Sun
    start_time: time
    end_time: time
    slot_duration: int        # minutes


class AvailabilityReader(ABC):
    """Read-only interface for doctor availability queries.

    Implemented in doctors/infrastructure, consumed by appointments/application.
    """

    @abstractmethod
    async def get_blocks(
        self, doctor_id: str, day_of_week: int
    ) -> List[AvailabilityBlock]:
        """Get availability blocks for a doctor on a specific day of week."""
        ...

    @abstractmethod
    async def has_exception(self, doctor_id: str, target_date: date) -> bool:
        """Check if the doctor has an exception (day off) on the given date."""
        ...

    @abstractmethod
    async def get_available_dows(self, doctor_id: str) -> Set[int]:
        """Get distinct day_of_week values where the doctor has availability."""
        ...

    @abstractmethod
    async def get_exception_dates(
        self, doctor_id: str, start: date, end: date
    ) -> Set[date]:
        """Get all exception dates for a doctor within a date range."""
        ...
