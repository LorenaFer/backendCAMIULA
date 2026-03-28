"""Schemas Pydantic para Límites y Excepciones de Despacho.

Alineados con DispatchLimit / DispatchException de inventory.ts.
"""

from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class DispatchLimitCreate(BaseModel):
    fk_medication_id: str
    monthly_max_quantity: int = Field(..., ge=1)
    applies_to: str = "all"


class DispatchLimitUpdate(BaseModel):
    monthly_max_quantity: Optional[int] = Field(None, ge=1)
    applies_to: Optional[str] = None
    active: Optional[bool] = None


class DispatchLimitResponse(BaseModel):
    """Espejo de la interfaz DispatchLimit del frontend."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    fk_medication_id: str
    monthly_max_quantity: int
    applies_to: str
    active: bool
    created_at: Optional[str]


class DispatchExceptionCreate(BaseModel):
    fk_patient_id: str
    fk_medication_id: str
    authorized_quantity: int = Field(..., ge=1)
    valid_from: date
    valid_until: date
    reason: str = Field(..., max_length=500)
    authorized_by: Optional[str] = Field(None, max_length=200)


class DispatchExceptionResponse(BaseModel):
    """Espejo de la interfaz DispatchException del frontend."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    fk_patient_id: str
    fk_medication_id: str
    authorized_quantity: int
    valid_from: str
    valid_until: str
    reason: str
    authorized_by: Optional[str]
    created_at: Optional[str]
