from __future__ import annotations
from dataclasses import dataclass
from datetime import date, time
from typing import Optional


@dataclass(frozen=True)
class CreateAppointmentDTO:
    patient_id: str
    doctor_id: str
    specialty_id: str
    appointment_date: date
    start_time: time
    end_time: time
    duration_minutes: int
    is_first_visit: bool
    reason: Optional[str] = None
    observations: Optional[str] = None


@dataclass(frozen=True)
class ChangeAppointmentStatusDTO:
    appointment_id: str
    new_status: str
