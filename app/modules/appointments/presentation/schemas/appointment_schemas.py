"""Pydantic schemas for the Appointment resource."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ---- Input ----


class AppointmentCreate(BaseModel):
    fk_patient_id: str = Field(..., max_length=36)
    fk_doctor_id: str = Field(..., max_length=36)
    fk_specialty_id: str = Field(..., max_length=36)
    appointment_date: str = Field(..., description="ISO date YYYY-MM-DD")
    start_time: str = Field(..., max_length=5, description="HH:MM")
    end_time: str = Field(..., max_length=5, description="HH:MM")
    duration_minutes: int = Field(..., ge=1)
    is_first_visit: bool = False
    reason: Optional[str] = None
    observations: Optional[str] = None


class AppointmentStatusUpdate(BaseModel):
    new_status: str = Field(..., max_length=20)


# ---- Output ----


class AppointmentResponse(BaseModel):
    """Full appointment response with embedded patient+doctor data."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    fk_patient_id: str
    fk_doctor_id: str
    fk_specialty_id: str
    appointment_date: Optional[str] = None
    start_time: str
    end_time: str
    duration_minutes: int
    is_first_visit: bool
    reason: Optional[str] = None
    observations: Optional[str] = None
    appointment_status: str
    patient_name: Optional[str] = None
    patient_cedula: Optional[str] = None
    doctor_name: Optional[str] = None
    specialty_name: Optional[str] = None
    patient_university_relation: Optional[str] = None
    created_at: Optional[str] = None


class SlotResponse(BaseModel):
    start_time: str
    end_time: str
    available: bool


class CheckSlotResponse(BaseModel):
    occupied: bool


class CitasStats(BaseModel):
    total: int
    by_status: Dict[str, int]
    by_specialty: List[Dict[str, Any]]
    by_doctor: List[Dict[str, Any]]
    first_time_count: int
    returning_count: int
    by_patient_type: Dict[str, int]
    daily_trend: List[int]
    peak_hours: List[Dict[str, Any]]
