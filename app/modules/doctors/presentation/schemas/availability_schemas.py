"""Pydantic schemas for DoctorAvailability resource."""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# --- Input ---


class AvailabilityCreate(BaseModel):
    day_of_week: int = Field(..., ge=0, le=6)
    start_time: str = Field(..., max_length=5, description="HH:MM format")
    end_time: str = Field(..., max_length=5, description="HH:MM format")
    slot_duration: int = Field(30, ge=5, le=120)


class AvailabilityUpdate(BaseModel):
    day_of_week: Optional[int] = Field(None, ge=0, le=6)
    start_time: Optional[str] = Field(None, max_length=5)
    end_time: Optional[str] = Field(None, max_length=5)
    slot_duration: Optional[int] = Field(None, ge=5, le=120)


# --- Output ---


class AvailabilityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    fk_doctor_id: str
    day_of_week: int
    start_time: str
    end_time: str
    slot_duration: int
    created_at: Optional[str] = None


class ExceptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    fk_doctor_id: str
    exception_date: str
    reason: Optional[str] = None
    created_at: Optional[str] = None
