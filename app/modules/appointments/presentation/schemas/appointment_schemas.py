"""Pydantic schemas for the Appointment resource."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class AppointmentCreate(BaseModel):
    """Create a new appointment."""

    fk_patient_id: str = Field(..., max_length=36, description="Patient UUID", example="a1b2c3d4-e5f6-7890-abcd-1234567890ab")
    fk_doctor_id: str = Field(..., max_length=36, description="Doctor UUID", example="d1e2f3a4-b5c6-7890-abcd-1234567890ab")
    fk_specialty_id: str = Field(..., max_length=36, description="Specialty UUID", example="f1e2d3c4-b5a6-7890-abcd-1234567890ab")
    appointment_date: str = Field(..., description="Appointment date (ISO YYYY-MM-DD)", example="2026-04-15")
    start_time: str = Field(..., max_length=5, description="Start time (HH:MM, 24h)", example="09:00")
    end_time: str = Field(..., max_length=5, description="End time (HH:MM, 24h)", example="09:30")
    duration_minutes: int = Field(..., ge=1, description="Duration in minutes (60 for new, 30 for returning)", example=30)
    is_first_visit: bool = Field(False, description="True if first-time patient visit", example=False)
    reason: Optional[str] = Field(None, description="Reason for visit", example="Consulta general")
    observations: Optional[str] = Field(None, description="Additional notes", example="Paciente refiere dolor de cabeza")
    client_token: Optional[str] = Field(None, max_length=36, description="Client-generated UUID for idempotent retries (safe against network microcuts)", example="b3f1c2a4-1234-4abc-9def-0123456789ab")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "fk_patient_id": "a1b2c3d4-e5f6-7890-abcd-1234567890ab",
            "fk_doctor_id": "d1e2f3a4-b5c6-7890-abcd-1234567890ab",
            "fk_specialty_id": "f1e2d3c4-b5a6-7890-abcd-1234567890ab",
            "appointment_date": "2026-04-15", "start_time": "09:00", "end_time": "09:30",
            "duration_minutes": 30, "reason": "Consulta general",
        }
    })


class AppointmentStatusUpdate(BaseModel):
    """Transition an appointment to a new status."""

    new_status: str = Field(..., max_length=20, description="Target status. Valid: pendiente, confirmada, cancelada, atendida, no_asistio", example="confirmada")


class AppointmentResponse(BaseModel):
    """Full appointment with embedded patient and doctor data."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(description="Appointment UUID", example="c1d2e3f4-a5b6-7890-abcd-1234567890ab")
    fk_patient_id: str = Field(description="Patient UUID", example="a1b2c3d4-e5f6-7890-abcd-1234567890ab")
    fk_doctor_id: str = Field(description="Doctor UUID", example="d1e2f3a4-b5c6-7890-abcd-1234567890ab")
    fk_specialty_id: str = Field(description="Specialty UUID", example="f1e2d3c4-b5a6-7890-abcd-1234567890ab")
    appointment_date: Optional[str] = Field(None, description="Date (ISO)", example="2026-04-15")
    start_time: str = Field(description="Start time (HH:MM)", example="09:00")
    end_time: str = Field(description="End time (HH:MM)", example="09:30")
    duration_minutes: int = Field(description="Duration in minutes", example=30)
    is_first_visit: bool = Field(description="First-time visit flag", example=False)
    reason: Optional[str] = Field(None, description="Visit reason", example="Consulta general")
    observations: Optional[str] = Field(None, description="Notes")
    appointment_status: str = Field(description="Current status: pendiente, confirmada, atendida, cancelada, no_asistio", example="pendiente")
    patient_name: Optional[str] = Field(None, description="Patient full name (resolved via JOIN)", example="Juan Perez")
    patient_dni: Optional[str] = Field(None, description="Patient national ID", example="V-12345678")
    patient_nhm: Optional[int] = Field(None, description="Patient hospital medical number", example=1024)
    doctor_name: Optional[str] = Field(None, description="Doctor full name", example="Dr. Carlos Mendez")
    specialty_name: Optional[str] = Field(None, description="Specialty name", example="Medicina General")
    patient_university_relation: Optional[str] = Field(None, description="Patient relation with ULA", example="estudiante")
    created_at: Optional[str] = Field(None, description="Creation timestamp", example="2026-04-10T10:00:00+00:00")


class SlotResponse(BaseModel):
    """Available time slot for scheduling."""

    start_time: str = Field(description="Slot start (HH:MM)", example="09:00")
    end_time: str = Field(description="Slot end (HH:MM)", example="09:30")
    available: bool = Field(description="True if the slot is not occupied", example=True)


class CheckSlotResponse(BaseModel):
    """Result of slot availability check."""

    occupied: bool = Field(description="True if the slot is already taken", example=False)


class CitasStats(BaseModel):
    """Aggregated appointment statistics."""

    total: int = Field(description="Total appointments in the period", example=150)
    by_status: Dict[str, int] = Field(description="Count by status", example={"pendiente": 30, "confirmada": 50, "atendida": 60, "cancelada": 10})
    by_specialty: List[Dict[str, Any]] = Field(description="Count by specialty", example=[{"specialty": "Medicina General", "count": 80}])
    by_doctor: List[Dict[str, Any]] = Field(description="Count by doctor", example=[{"doctor": "Dr. Mendez", "count": 45}])
    first_time_count: int = Field(description="First-time patients", example=40)
    returning_count: int = Field(description="Returning patients", example=110)
    by_patient_type: Dict[str, int] = Field(description="Count by university relation", example={"estudiante": 90, "personal": 30})
    daily_trend: List[int] = Field(description="Daily appointment count trend", example=[12, 15, 18, 20, 14, 16, 22])
    peak_hours: List[Dict[str, Any]] = Field(description="Busiest hours", example=[{"hour": 9, "count": 25}, {"hour": 10, "count": 30}])
