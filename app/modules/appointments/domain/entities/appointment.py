"""Domain entity: Appointment."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Appointment:
    id: str
    fk_patient_id: str
    fk_doctor_id: str
    fk_specialty_id: str
    appointment_date: str
    start_time: str
    end_time: str
    duration_minutes: int
    is_first_visit: bool
    appointment_status: str
    reason: Optional[str] = None
    observations: Optional[str] = None
    status: Optional[str] = None
    created_at: Optional[str] = None
    created_by: Optional[str] = None
    # Embedded cross-module data (populated by joins)
    patient_name: Optional[str] = None
    patient_dni: Optional[str] = None
    doctor_name: Optional[str] = None
    specialty_name: Optional[str] = None
    patient_university_relation: Optional[str] = None
