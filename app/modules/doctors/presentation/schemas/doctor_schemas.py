"""Pydantic schemas for the Doctor resource."""

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class DoctorResponse(BaseModel):
    """Doctor profile with embedded specialty."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(description="Doctor UUID", example="d1e2f3a4-b5c6-7890-abcd-1234567890ab")
    fk_user_id: str = Field(description="Linked user account UUID", example="a1b2c3d4-e5f6-7890-abcd-1234567890ab")
    fk_specialty_id: str = Field(description="Specialty UUID", example="f1e2d3c4-b5a6-7890-abcd-1234567890ab")
    first_name: str = Field(description="Doctor's first name", example="Carlos")
    last_name: str = Field(description="Doctor's last name", example="Mendez")
    doctor_status: str = Field(description="Status: ACTIVE or INACTIVE", example="ACTIVE")
    specialty_name: Optional[str] = Field(None, description="Specialty name (resolved via JOIN)", example="Medicina General")
    created_at: Optional[str] = Field(None, description="Creation timestamp", example="2026-01-10T08:00:00+00:00")


class DoctorOptionResponse(BaseModel):
    """Lightweight doctor for dropdown selects."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(description="Doctor UUID", example="d1e2f3a4-b5c6-7890-abcd-1234567890ab")
    first_name: str = Field(description="First name", example="Carlos")
    last_name: str = Field(description="Last name", example="Mendez")
    fk_specialty_id: str = Field(description="Specialty UUID", example="f1e2d3c4-b5a6-7890-abcd-1234567890ab")
    specialty_name: Optional[str] = Field(None, description="Specialty name", example="Medicina General")
    work_days: List[int] = Field(default=[], description="Days of week with availability (1=Mon, 5=Fri)", example=[1, 2, 3, 4, 5])
