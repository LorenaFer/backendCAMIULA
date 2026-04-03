"""Pydantic schemas for the Patient resource.

Internal fields are in English. Frontend-facing aliases map to the
Spanish keys expected by the frontend (docs/api/02-patients.md).
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# ─── Input ────────────────────────────────────────────────────


class PatientCreate(BaseModel):
    cedula: str = Field(..., max_length=20)
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)
    university_relation: str = Field(..., max_length=20)
    sex: Optional[str] = Field(None, max_length=1)
    birth_date: Optional[str] = Field(None, description="ISO date YYYY-MM-DD")
    birth_place: Optional[str] = Field(None, max_length=200)
    marital_status: Optional[str] = Field(None, max_length=20)
    religion: Optional[str] = Field(None, max_length=100)
    origin: Optional[str] = Field(None, max_length=200)
    home_address: Optional[str] = Field(None, max_length=300)
    phone: Optional[str] = Field(None, max_length=20)
    profession: Optional[str] = Field(None, max_length=100)
    current_occupation: Optional[str] = Field(None, max_length=100)
    work_address: Optional[str] = Field(None, max_length=300)
    economic_classification: Optional[str] = Field(None, max_length=50)
    family_relationship: Optional[str] = Field(None, max_length=20)
    fk_holder_patient_id: Optional[str] = Field(None, max_length=36)
    medical_data: Optional[dict] = None
    emergency_contact: Optional[dict] = None


class PatientRegister(BaseModel):
    """Extended registration from ULA portal."""

    cedula: str = Field(..., max_length=20)
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)
    university_relation: str = Field(..., max_length=20)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=200)
    sex: Optional[str] = Field(None, max_length=1)
    birth_date: Optional[str] = None
    country: Optional[str] = Field(None, max_length=100)
    state_geo: Optional[str] = Field(None, max_length=100)
    city: Optional[str] = Field(None, max_length=100)
    marital_status: Optional[str] = Field(None, max_length=20)
    blood_type: Optional[str] = Field(None, max_length=10)
    religion: Optional[str] = Field(None, max_length=100)
    economic_classification: Optional[str] = Field(None, max_length=50)
    profession: Optional[str] = Field(None, max_length=100)
    current_occupation: Optional[str] = Field(None, max_length=100)
    family_relationship: Optional[str] = Field(None, max_length=20)
    holder_cedula: Optional[str] = Field(None, max_length=20)
    home_address: Optional[str] = Field(None, max_length=300)
    work_address: Optional[str] = Field(None, max_length=300)
    emergency_name: Optional[str] = Field(None, max_length=200)
    emergency_relationship: Optional[str] = Field(None, max_length=50)
    emergency_phone: Optional[str] = Field(None, max_length=20)
    emergency_address: Optional[str] = Field(None, max_length=300)
    allergies: Optional[str] = Field(None, max_length=500)
    medical_alerts: Optional[str] = Field(None, max_length=500)


# ─── Output ───────────────────────────────────────────────────


class PatientResponse(BaseModel):
    """Full patient entity response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    nhm: int
    cedula: str
    first_name: str
    last_name: str
    sex: Optional[str] = None
    birth_date: Optional[str] = None
    birth_place: Optional[str] = None
    marital_status: Optional[str] = None
    religion: Optional[str] = None
    origin: Optional[str] = None
    home_address: Optional[str] = None
    phone: Optional[str] = None
    profession: Optional[str] = None
    current_occupation: Optional[str] = None
    work_address: Optional[str] = None
    economic_classification: Optional[str] = None
    university_relation: str
    family_relationship: Optional[str] = None
    fk_holder_patient_id: Optional[str] = None
    medical_data: dict = {}
    emergency_contact: Optional[dict] = None
    is_new: bool
    created_at: Optional[str] = None


class PatientPublicResponse(BaseModel):
    """Public patient — no sensitive data."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    nhm: int
    first_name: str
    last_name: str
    university_relation: str
    is_new: bool


class MaxNhmResponse(BaseModel):
    max_nhm: int
