"""Schemas Pydantic para el recurso Receta Médica (Prescription).

Alineados con las interfaces Prescription / PrescriptionItem de inventory.ts.
"""

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.modules.inventory.presentation.schemas.medication_schemas import (
    MedicationOptionResponse,
)


class PrescriptionItemCreate(BaseModel):
    medication_id: str
    quantity_prescribed: int = Field(..., ge=1)
    dosage_instructions: Optional[str] = Field(None, max_length=300)
    duration_days: Optional[int] = Field(None, ge=1)


class PrescriptionCreate(BaseModel):
    fk_appointment_id: str
    fk_patient_id: str
    fk_doctor_id: Optional[str] = None
    notes: Optional[str] = Field(None, max_length=500)
    items: List[PrescriptionItemCreate] = Field(..., min_length=1)


class PrescriptionItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    fk_medication_id: str
    quantity_prescribed: int
    dosage_instructions: Optional[str]
    duration_days: Optional[int]


class PrescriptionResponse(BaseModel):
    """Espejo de la interfaz Prescription del frontend."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    prescription_number: str
    fk_appointment_id: str
    fk_patient_id: str
    fk_doctor_id: str
    prescription_date: str
    notes: Optional[str]
    prescription_status: str
    items: List[PrescriptionItemResponse]
    created_at: Optional[str]
