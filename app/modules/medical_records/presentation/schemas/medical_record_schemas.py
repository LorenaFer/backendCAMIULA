"""Pydantic schemas for Medical Records."""

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


# --- Input ---


class MedicalRecordUpsert(BaseModel):
    fk_appointment_id: str = Field(..., max_length=36)
    fk_patient_id: str = Field(..., max_length=36)
    fk_doctor_id: str = Field(..., max_length=36)
    evaluation: Optional[Any] = None
    schema_id: Optional[str] = Field(None, max_length=36)
    schema_version: Optional[str] = Field(None, max_length=50)


class MarkPreparedBody(BaseModel):
    prepared_by: str = Field(..., max_length=36)


# --- Output ---


class MedicalRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    fk_appointment_id: str
    fk_patient_id: str
    fk_doctor_id: str
    evaluation: Optional[Any] = None
    is_prepared: bool
    prepared_at: Optional[str] = None
    prepared_by: Optional[str] = None
    schema_id: Optional[str] = None
    schema_version: Optional[str] = None
    status: str
    created_at: Optional[str] = None
    created_by: Optional[str] = None
    updated_at: Optional[str] = None
    updated_by: Optional[str] = None


class PatientHistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    date: Optional[str] = None
    specialty: Optional[str] = None
    doctor_name: Optional[str] = None
    diagnosis_description: Optional[str] = None
    diagnosis_code: Optional[str] = None
