"""Schemas Pydantic para el recurso Lote (Batch).

Alineados con la interfaz Batch de inventory.ts.
"""

from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.modules.inventory.presentation.schemas.medication_schemas import (
    MedicationOptionResponse,
)


class BatchCreate(BaseModel):
    fk_medication_id: str
    lot_number: str = Field(..., max_length=100)
    expiration_date: date
    quantity_received: int = Field(..., ge=1)
    received_at: date
    fk_supplier_id: Optional[str] = None
    fk_purchase_order_id: Optional[str] = None
    unit_cost: Optional[float] = Field(None, ge=0)


class BatchStatusUpdate(BaseModel):
    batch_status: str


class BatchResponse(BaseModel):
    """Espejo de la interfaz Batch del frontend."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    fk_medication_id: str
    fk_supplier_id: Optional[str]
    lot_number: str
    expiration_date: str
    quantity_received: int
    quantity_available: int
    unit_cost: Optional[float]
    batch_status: str
    received_at: str
