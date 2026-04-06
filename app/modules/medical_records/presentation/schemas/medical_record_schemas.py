"""Pydantic schemas for Medical Records."""

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class MedicalRecordUpsert(BaseModel):
    """Create or update a medical record for an appointment."""

    fk_appointment_id: str = Field(..., max_length=36, description="Appointment UUID", example="c1d2e3f4-a5b6-7890-abcd-1234567890ab")
    fk_patient_id: str = Field(..., max_length=36, description="Patient UUID", example="a1b2c3d4-e5f6-7890-abcd-1234567890ab")
    fk_doctor_id: str = Field(..., max_length=36, description="Doctor UUID", example="d1e2f3a4-b5c6-7890-abcd-1234567890ab")
    evaluation: Optional[Any] = Field(None, description="Clinical evaluation (JSONB). Structure matches the specialty's form schema", example={"motivo_consulta": "Dolor de cabeza", "diagnostico": {"code": "R51", "description": "Cefalea"}})
    schema_id: Optional[str] = Field(None, max_length=36, description="Form schema UUID used for this evaluation")
    schema_version: Optional[str] = Field(None, max_length=50, description="Schema version", example="1.0")


class MarkPreparedBody(BaseModel):
    """Mark a record as prepared by nursing staff."""

    prepared_by: str = Field(..., max_length=36, description="UUID of the nurse/staff who prepared the record", example="n1u2r3s4-e5f6-7890-abcd-1234567890ab")


class MedicalRecordResponse(BaseModel):
    """Full medical record with evaluation data."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(description="Record UUID", example="r1e2c3d4-o5r6-7890-abcd-1234567890ab")
    fk_appointment_id: str = Field(description="Appointment UUID")
    fk_patient_id: str = Field(description="Patient UUID")
    fk_doctor_id: str = Field(description="Doctor UUID")
    evaluation: Optional[Any] = Field(None, description="Clinical evaluation (JSONB)")
    is_prepared: bool = Field(description="True if nursing staff has completed pre-consultation", example=False)
    prepared_at: Optional[str] = Field(None, description="Preparation timestamp")
    prepared_by: Optional[str] = Field(None, description="Preparer UUID")
    schema_id: Optional[str] = Field(None, description="Form schema UUID")
    schema_version: Optional[str] = Field(None, description="Schema version")
    status: str = Field(description="Record status: A (active)", example="A")
    created_at: Optional[str] = Field(None, description="Creation timestamp", example="2026-04-15T10:30:00+00:00")
    created_by: Optional[str] = Field(None, description="Creator UUID")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")
    updated_by: Optional[str] = Field(None, description="Last updater UUID")


class PatientHistoryItem(BaseModel):
    """Summary of a past consultation."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(description="Medical record UUID")
    date: Optional[str] = Field(None, description="Consultation date", example="2026-04-10")
    specialty: Optional[str] = Field(None, description="Specialty name", example="Medicina General")
    doctor_name: Optional[str] = Field(None, description="Doctor name", example="Dr. Carlos Mendez")
    diagnosis_description: Optional[str] = Field(None, description="Primary diagnosis", example="Hipertension arterial")
    diagnosis_code: Optional[str] = Field(None, description="CIE-10 code", example="I10")
