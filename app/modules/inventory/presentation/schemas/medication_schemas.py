"""Schemas Pydantic para el recurso Medicamento.

Los campos están alineados 1:1 con la interfaz Medication de
frontend/src/lib/shared/types/inventory.ts.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# ─── Entrada ──────────────────────────────────────────────────


class MedicationCreate(BaseModel):
    code: str = Field(..., max_length=50)
    generic_name: str = Field(..., max_length=200)
    pharmaceutical_form: str = Field(..., max_length=100)
    unit_measure: str = Field(..., max_length=50)
    controlled_substance: bool
    requires_refrigeration: bool
    commercial_name: Optional[str] = Field(None, max_length=200)
    concentration: Optional[str] = Field(None, max_length=100)
    therapeutic_class: Optional[str] = Field(None, max_length=100)


class MedicationUpdate(BaseModel):
    generic_name: Optional[str] = Field(None, max_length=200)
    commercial_name: Optional[str] = Field(None, max_length=200)
    pharmaceutical_form: Optional[str] = Field(None, max_length=100)
    concentration: Optional[str] = Field(None, max_length=100)
    unit_measure: Optional[str] = Field(None, max_length=50)
    therapeutic_class: Optional[str] = Field(None, max_length=100)
    controlled_substance: Optional[bool] = None
    requires_refrigeration: Optional[bool] = None
    medication_status: Optional[str] = None


# ─── Salida ───────────────────────────────────────────────────


class MedicationResponse(BaseModel):
    """Espejo exacto de la interfaz Medication del frontend."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    code: str
    generic_name: str
    commercial_name: Optional[str]
    pharmaceutical_form: str
    concentration: Optional[str]
    unit_measure: str
    therapeutic_class: Optional[str]
    controlled_substance: bool
    requires_refrigeration: bool
    medication_status: str
    current_stock: int
    created_at: Optional[str]


class MedicationOptionResponse(BaseModel):
    """Espejo exacto de la interfaz MedicationOption del frontend."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    code: str
    generic_name: str
    pharmaceutical_form: str
    unit_measure: str
    current_stock: int
