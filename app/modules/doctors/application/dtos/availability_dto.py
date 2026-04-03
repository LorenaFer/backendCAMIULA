"""DTOs for Availability use cases."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class CreateAvailabilityDTO:
    fk_doctor_id: str
    day_of_week: int
    start_time: str
    end_time: str
    slot_duration: int = 30


@dataclass
class UpdateAvailabilityDTO:
    day_of_week: Optional[int] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    slot_duration: Optional[int] = None
