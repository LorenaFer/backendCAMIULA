"""Domain entity: DoctorAvailability."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class DoctorAvailability:
    id: str
    fk_doctor_id: str
    day_of_week: int
    start_time: str
    end_time: str
    slot_duration: int = 30
    status: Optional[str] = None
    created_at: Optional[str] = None
    created_by: Optional[str] = None
