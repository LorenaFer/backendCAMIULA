"""Schemas Pydantic para el recurso Despacho (Dispatch).

Alineados con las interfaces Dispatch, DispatchValidation de inventory.ts.
"""

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class DispatchCreate(BaseModel):
    fk_prescription_id: str
    patient_type: str = Field("all", description="Tipo de beneficiario: all, student, employee, professor")
    notes: Optional[str] = Field(None, max_length=500)


class DispatchItemResponse(BaseModel):
    """Espejo de la interfaz DispatchItem del frontend."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    fk_batch_id: str
    fk_medication_id: str
    quantity_dispatched: int


class DispatchResponse(BaseModel):
    """Espejo de la interfaz Dispatch del frontend."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    fk_prescription_id: str
    fk_patient_id: str
    fk_pharmacist_id: str
    dispatch_date: str
    notes: Optional[str]
    dispatch_status: str
    items: List[DispatchItemResponse]
    created_at: Optional[str]


class DispatchValidationItemResponse(BaseModel):
    """Espejo de la interfaz DispatchValidationItem del frontend."""

    medication_id: str
    generic_name: str
    quantity_prescribed: int
    quantity_available: int
    monthly_limit: Optional[int]
    monthly_used: int
    monthly_remaining: Optional[int]
    has_exception: bool
    can_dispatch: bool
    block_reason: Optional[str]


class DispatchValidationResponse(BaseModel):
    """Espejo de la interfaz DispatchValidation del frontend."""

    can_dispatch: bool
    prescription_id: str
    patient_id: str
    items: List[DispatchValidationItemResponse]
