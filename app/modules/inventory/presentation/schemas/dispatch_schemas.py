"""Pydantic schemas for Dispatches (pharmacy dispensing)."""

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class DispatchCreate(BaseModel):
    """Execute a pharmacy dispatch for a prescription."""

    fk_prescription_id: str = Field(description="Prescription UUID to dispense", example="rx1a2b3c-d4e5-6789-abcd-1234567890ab")
    patient_type: str = Field("all", description="Beneficiary type for limit checking: all, student, employee, professor", example="student")
    notes: Optional[str] = Field(None, max_length=500, description="Dispatch notes", example="Paciente retira personalmente")


class DispatchItemResponse(BaseModel):
    """Individual item in a dispatch with batch traceability."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(description="Dispatch item UUID")
    fk_batch_id: str = Field(description="Source batch UUID (FEFO allocation)")
    fk_medication_id: str = Field(description="Medication UUID")
    quantity_dispatched: int = Field(description="Units dispensed from this batch", example=10)
    medication_name: Optional[str] = Field(None, description="Medication generic name (joined)", example="Amoxicilina 500mg")
    medication_form: Optional[str] = Field(None, description="Pharmaceutical form (joined)", example="Cápsula")
    batch_number: Optional[str] = Field(None, description="Source batch lot number (joined)", example="LOT-2026-A1")
    expiration_date: Optional[str] = Field(None, description="Batch expiration date ISO (joined)", example="2027-08-15")


class DispatchResponse(BaseModel):
    """Completed pharmacy dispatch."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(description="Dispatch UUID", example="dp1a2b3c-d4e5-6789-abcd-1234567890ab")
    fk_prescription_id: str = Field(description="Prescription UUID")
    fk_patient_id: str = Field(description="Patient UUID")
    fk_pharmacist_id: str = Field(description="Pharmacist user UUID")
    dispatch_date: str = Field(description="Dispatch timestamp (ISO)", example="2026-04-15T14:30:00+00:00")
    notes: Optional[str] = Field(None, description="Notes")
    dispatch_status: str = Field(description="Status: pending, completed, cancelled", example="completed")
    items: List[DispatchItemResponse] = Field(description="Dispatched items with batch allocation")
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    # Enriched display fields
    prescription_number: Optional[str] = Field(None, description="Prescription number (e.g. RX-2026-00001)", example="RX-2026-00001")
    patient_full_name: Optional[str] = Field(None, description="Patient full name", example="Juan Perez")
    pharmacist_full_name: Optional[str] = Field(None, description="Pharmacist full name", example="Pedro Farmacia")


class DispatchValidationItemResponse(BaseModel):
    """Pre-validation result for a single medication."""

    medication_id: str = Field(description="Medication UUID")
    generic_name: str = Field(description="Medication name", example="Amoxicilina")
    quantity_prescribed: int = Field(description="Prescribed quantity", example=30)
    quantity_available: int = Field(description="Available stock (FEFO)", example=350)
    monthly_limit: Optional[int] = Field(None, description="Monthly limit for this patient type", example=60)
    monthly_used: int = Field(description="Units already dispatched this month", example=0)
    monthly_remaining: Optional[int] = Field(None, description="Remaining under limit", example=60)
    has_exception: bool = Field(description="Patient has an authorized exception", example=False)
    can_dispatch: bool = Field(description="True if dispatch is allowed", example=True)
    block_reason: Optional[str] = Field(None, description="Reason if dispatch is blocked")


class DispatchValidationResponse(BaseModel):
    """Pre-validation result for a full prescription dispatch."""

    can_dispatch: bool = Field(description="True if all items can be dispatched", example=True)
    prescription_id: str = Field(description="Prescription UUID")
    patient_id: str = Field(description="Patient UUID")
    items: List[DispatchValidationItemResponse] = Field(description="Per-item validation results")
