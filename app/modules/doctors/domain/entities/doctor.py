"""Domain entity: Doctor."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Doctor:
    id: str
    fk_user_id: str
    fk_specialty_id: str
    first_name: str
    last_name: str
    doctor_status: str
    specialty_name: Optional[str] = None
    work_days: Optional[List[int]] = field(default_factory=list)
    status: Optional[str] = None
    created_at: Optional[str] = None
    created_by: Optional[str] = None
