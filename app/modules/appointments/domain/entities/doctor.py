from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional
from uuid import uuid4


@dataclass
class Doctor:
    first_name: str
    last_name: str
    user_id: str
    specialty_id: str
    id: str = field(default_factory=lambda: str(uuid4()))
    doctor_status: str = "ACTIVE"
    specialty_name: Optional[str] = None
    work_days: List[int] = field(default_factory=list)

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def display_name(self) -> str:
        return f"Dr. {self.first_name} {self.last_name}"
