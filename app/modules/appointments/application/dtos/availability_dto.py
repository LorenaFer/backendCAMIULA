from __future__ import annotations
from dataclasses import dataclass
from datetime import time
from typing import Optional


@dataclass(frozen=True)
class CreateAvailabilityBlockDTO:
    doctor_id: str
    day_of_week: int
    start_time: time
    end_time: time
    slot_duration: int


@dataclass(frozen=True)
class UpdateAvailabilityBlockDTO:
    block_id: str
    start_time: Optional[time] = None
    end_time: Optional[time] = None
