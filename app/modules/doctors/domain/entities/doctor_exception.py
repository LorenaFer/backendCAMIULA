"""Domain entity: DoctorException."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class DoctorException:
    id: str
    fk_doctor_id: str
    exception_date: str
    reason: Optional[str] = None
    status: Optional[str] = None
    created_at: Optional[str] = None
    created_by: Optional[str] = None
