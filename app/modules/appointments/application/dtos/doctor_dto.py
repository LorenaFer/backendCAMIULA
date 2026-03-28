from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class DoctorOptionDTO:
    id: str
    full_name: str
    specialty: str
    specialty_id: str
    work_days: List[int]
