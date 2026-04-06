"""Pydantic schemas for Prescriptions."""

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.modules.inventory.presentation.schemas.medication_schemas import (
    MedicationOptionResponse,
)


class PrescriptionItemCreate(BaseModel):
    """A single medication item in a prescription."""

    medication_id: str = Field(description="Medication UUID", example="m1e2d3c4-b5a6-7890-abcd-1234567890ab")
    quantity_prescribed: int = Field(..., ge=1, description="Units prescribed", example=30)
    dosage_instructions: Optional[str] = Field(None, max_length=300, description="Dosage instructions", example="1 tablet every 8 hours")
    duration_days: Optional[int] = Field(None, ge=1, description="Treatment duration in days", example=7)


class PrescriptionCreate(BaseModel):
    """Create a new prescription for an appointment."""

    fk_appointment_id: str = Field(description="Appointment UUID", example="c1d2e3f4-a5b6-7890-abcd-1234567890ab")
    fk_patient_id: str = Field(description="Patient UUID", example="a1b2c3d4-e5f6-7890-abcd-1234567890ab")
    fk_doctor_id: Optional[str] = Field(None, description="Doctor UUID (auto-resolved from appointment if omitted)")
    notes: Optional[str] = Field(None, max_length=500, description="Prescription notes", example="Tomar con alimentos")
    items: List[PrescriptionItemCreate] = Field(..., min_length=1, description="Prescribed medications (at least 1)")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "fk_appointment_id": "c1d2e3f4-a5b6-7890-abcd-1234567890ab",
            "fk_patient_id": "a1b2c3d4-e5f6-7890-abcd-1234567890ab",
            "items": [{"medication_id": "m1e2d3c4-b5a6-7890-abcd-1234567890ab", "quantity_prescribed": 30, "dosage_instructions": "1 tablet every 8 hours", "duration_days": 7}],
        }
    })


class MedicationEmbedResponse(BaseModel):
    """Embedded medication in prescription item."""

    model_config = ConfigDict(from_attributes=True)
    id: str = Field(description="Medication UUID")
    code: str = Field(description="Code", example="MED-001")
    generic_name: str = Field(description="Generic name", example="Amoxicilina")
    pharmaceutical_form: str = Field(description="Form", example="tablet")
    unit_measure: str = Field(description="Unit", example="unit")


class PrescriptionItemResponse(BaseModel):
    """Prescription item with dispensing status."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(description="Item UUID")
    fk_medication_id: str = Field(description="Medication UUID")
    medication: Optional[MedicationEmbedResponse] = Field(None, description="Embedded medication")
    quantity_prescribed: int = Field(description="Prescribed quantity", example=30)
    dosage_instructions: Optional[str] = Field(None, description="Instructions", example="1 tablet every 8 hours")
    duration_days: Optional[int] = Field(None, description="Duration (days)", example=7)


class PrescriptionResponse(BaseModel):
    """Full prescription with items and medication details."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(description="Prescription UUID")
    prescription_number: str = Field(description="Auto-generated number", example="RX-2026-0001")
    fk_appointment_id: str = Field(description="Appointment UUID")
    fk_patient_id: str = Field(description="Patient UUID")
    fk_doctor_id: Optional[str] = Field(None, description="Doctor UUID")
    doctor_name: Optional[str] = Field(None, description="Doctor name (resolved via JOIN)", example="Dr. Carlos Mendez")
    prescription_date: Optional[str] = Field(None, description="Issue date", example="2026-04-15")
    notes: Optional[str] = Field(None, description="Notes", example="Tomar con alimentos")
    prescription_status: str = Field(description="Status: draft, issued, dispensed, cancelled", example="issued")
    items: List[PrescriptionItemResponse] = Field(default=[], description="Prescribed items")
    created_at: Optional[str] = Field(None, description="Creation timestamp")
