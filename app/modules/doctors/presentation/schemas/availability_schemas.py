"""Pydantic schemas for Doctor Availability and Exceptions."""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class AvailabilityCreate(BaseModel):
    """Create a time block when a doctor is available."""

    day_of_week: int = Field(..., ge=0, le=6, description="Day of week: 0=Sunday, 1=Monday, ..., 6=Saturday", example=1)
    start_time: str = Field(..., max_length=5, description="Block start time (HH:MM, 24h)", example="08:00")
    end_time: str = Field(..., max_length=5, description="Block end time (HH:MM, 24h)", example="12:00")
    slot_duration: int = Field(30, ge=5, le=120, description="Appointment slot duration in minutes", example=30)

    model_config = ConfigDict(json_schema_extra={
        "example": {"day_of_week": 1, "start_time": "08:00", "end_time": "12:00", "slot_duration": 30}
    })


class AvailabilityUpdate(BaseModel):
    """Update an availability block."""

    day_of_week: Optional[int] = Field(None, ge=0, le=6, description="Day of week", example=2)
    start_time: Optional[str] = Field(None, max_length=5, description="New start time", example="09:00")
    end_time: Optional[str] = Field(None, max_length=5, description="New end time", example="13:00")
    slot_duration: Optional[int] = Field(None, ge=5, le=120, description="New slot duration (minutes)", example=30)


class AvailabilityResponse(BaseModel):
    """Doctor availability time block."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(description="Availability block UUID", example="e1f2a3b4-c5d6-7890-abcd-1234567890ab")
    fk_doctor_id: str = Field(description="Doctor UUID", example="d1e2f3a4-b5c6-7890-abcd-1234567890ab")
    day_of_week: int = Field(description="Day of week (0=Sun, 1=Mon, ..., 6=Sat)", example=1)
    start_time: str = Field(description="Start time (HH:MM)", example="08:00")
    end_time: str = Field(description="End time (HH:MM)", example="12:00")
    slot_duration: int = Field(description="Slot duration in minutes", example=30)
    created_at: Optional[str] = Field(None, description="Creation timestamp", example="2026-01-10T08:00:00+00:00")


class ExceptionResponse(BaseModel):
    """Doctor day-off exception."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(description="Exception UUID", example="c1d2e3f4-a5b6-7890-abcd-1234567890ab")
    fk_doctor_id: str = Field(description="Doctor UUID", example="d1e2f3a4-b5c6-7890-abcd-1234567890ab")
    exception_date: str = Field(description="Date of the exception (ISO YYYY-MM-DD)", example="2026-04-15")
    reason: Optional[str] = Field(None, description="Reason for the day off", example="Conferencia medica")
    created_at: Optional[str] = Field(None, example="2026-01-10T08:00:00+00:00")
