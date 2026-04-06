"""Pydantic schemas for Doctor resource."""

from typing import List, Optional

from pydantic import BaseModel, ConfigDict


# --- Output ---


class DoctorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    fk_user_id: str
    fk_specialty_id: str
    first_name: str
    last_name: str
    doctor_status: str
    specialty_name: Optional[str] = None
    created_at: Optional[str] = None


class DoctorOptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    first_name: str
    last_name: str
    fk_specialty_id: str
    specialty_name: Optional[str] = None
    work_days: List[int] = []
