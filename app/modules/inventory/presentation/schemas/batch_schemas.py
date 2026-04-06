"""Pydantic schemas for the Batch (Lot) resource."""

from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.modules.inventory.presentation.schemas.medication_schemas import (
    MedicationOptionResponse,
)


class BatchCreate(BaseModel):
    """Register a new inventory batch."""

    fk_medication_id: str = Field(description="Medication UUID", example="m1e2d3c4-b5a6-7890-abcd-1234567890ab")
    lot_number: str = Field(..., max_length=100, description="Manufacturer lot number", example="LOT-2026-AMX-001")
    expiration_date: date = Field(description="Expiration date (ISO YYYY-MM-DD)", example="2027-06-30")
    quantity_received: int = Field(..., ge=1, description="Units received", example=500)
    received_at: date = Field(description="Date of reception", example="2026-04-01")
    fk_supplier_id: Optional[str] = Field(None, description="Supplier UUID")
    fk_purchase_order_id: Optional[str] = Field(None, description="Purchase order UUID")
    unit_cost: Optional[float] = Field(None, ge=0, description="Cost per unit", example=2.50)


class BatchStatusUpdate(BaseModel):
    """Update batch status."""

    batch_status: str = Field(description="New status: available, depleted, expired, quarantine", example="quarantine")


class BatchResponse(BaseModel):
    """Inventory batch (lot) details."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(description="Batch UUID", example="b1a2c3d4-e5f6-7890-abcd-1234567890ab")
    fk_medication_id: str = Field(description="Medication UUID", example="m1e2d3c4-b5a6-7890-abcd-1234567890ab")
    fk_supplier_id: Optional[str] = Field(None, description="Supplier UUID")
    lot_number: str = Field(description="Lot number", example="LOT-2026-AMX-001")
    expiration_date: str = Field(description="Expiration date (ISO)", example="2027-06-30")
    quantity_received: int = Field(description="Original units received", example=500)
    quantity_available: int = Field(description="Current available units", example=350)
    unit_cost: Optional[float] = Field(None, description="Cost per unit", example=2.50)
    batch_status: str = Field(description="Status: available, depleted, expired, quarantine", example="available")
    received_at: str = Field(description="Reception date", example="2026-04-01")
