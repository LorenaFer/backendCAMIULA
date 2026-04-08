"""DTOs for the appointments module."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class CreateAppointmentDTO:
    fk_patient_id: str
    fk_doctor_id: str
    fk_specialty_id: str
    appointment_date: str
    start_time: str
    end_time: str
    duration_minutes: int
    is_first_visit: bool = False
    reason: Optional[str] = None
    observations: Optional[str] = None
    client_token: Optional[str] = None


@dataclass
class UpdateStatusDTO:
    new_status: str
