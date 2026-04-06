"""Pydantic schemas for Purchase Orders."""

from datetime import date
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ─── Input ────────────────────────────────────────────────────


class PurchaseOrderItemCreate(BaseModel):
    """Item to include in a purchase order."""

    medication_id: str = Field(description="Medication UUID", example="m1e2d3c4-b5a6-7890-abcd-1234567890ab")
    quantity_ordered: int = Field(..., ge=1, description="Units to order", example=100)
    unit_cost: float = Field(..., ge=0, description="Cost per unit", example=2.50)


class PurchaseOrderCreate(BaseModel):
    """Create a new purchase order (draft status)."""

    fk_supplier_id: str = Field(description="Supplier UUID", example="s1e2d3c4-b5a6-7890-abcd-1234567890ab")
    expected_date: Optional[date] = Field(None, description="Expected delivery date", example="2026-05-01")
    notes: Optional[str] = Field(None, max_length=500, description="Additional notes", example="Urgente - stock critico")
    items: List[PurchaseOrderItemCreate] = Field(..., min_length=1, description="Items to order (at least 1)")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "fk_supplier_id": "s1e2d3c4-b5a6-7890-abcd-1234567890ab",
            "expected_date": "2026-05-01",
            "items": [{"medication_id": "m1e2d3c4-b5a6-7890-abcd-1234567890ab", "quantity_ordered": 100, "unit_cost": 2.50}],
        }
    })


class PurchaseOrderStatusUpdate(BaseModel):
    """Transition purchase order status."""

    order_status: str = Field(description="New status: draft, sent, partial, received, cancelled", example="sent")


class ReceiveItemInput(BaseModel):
    """Register a received item (creates a batch)."""

    purchase_order_item_id: str = Field(description="PO item UUID to receive against", example="i1a2b3c4-d5e6-7890-abcd-1234567890ab")
    quantity_received: int = Field(..., ge=1, description="Units actually received", example=100)
    lot_number: str = Field(..., max_length=100, description="Manufacturer lot number", example="LOT-2026-AMX-001")
    expiration_date: date = Field(description="Batch expiration date", example="2027-06-30")
    unit_cost: Optional[float] = Field(None, ge=0, description="Actual unit cost", example=2.50)


class ReceivePurchaseOrderInput(BaseModel):
    """Register received items for a purchase order."""

    items: List[ReceiveItemInput] = Field(..., min_length=1, description="Received items (at least 1)")


# ─── Embedded ─────────────────────────────────────────────────


class SupplierEmbedResponse(BaseModel):
    """Embedded supplier in PO response."""

    model_config = ConfigDict(from_attributes=True)
    id: str = Field(description="Supplier UUID")
    name: str = Field(description="Company name", example="Distribuidora Farmaceutica Nacional")
    rif: Optional[str] = Field(None, description="RIF", example="J-12345678-9")


class MedicationEmbedResponse(BaseModel):
    """Embedded medication in PO item response."""

    model_config = ConfigDict(from_attributes=True)
    id: str = Field(description="Medication UUID")
    code: str = Field(description="Medication code", example="MED-001")
    generic_name: str = Field(description="Generic name", example="Amoxicilina")
    pharmaceutical_form: str = Field(description="Form", example="tablet")
    unit_measure: str = Field(description="Unit", example="unit")


# ─── Output ───────────────────────────────────────────────────


class PurchaseOrderItemResponse(BaseModel):
    """PO line item with medication details."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(description="Item UUID")
    fk_medication_id: str = Field(description="Medication UUID")
    medication: Optional[MedicationEmbedResponse] = Field(None, description="Embedded medication details")
    quantity_ordered: int = Field(description="Units ordered", example=100)
    quantity_received: int = Field(description="Units received so far", example=0)
    unit_cost: Optional[float] = Field(None, description="Unit cost", example=2.50)
    item_status: str = Field(description="Item status: pending, partial, received, cancelled", example="pending")


class PurchaseOrderResponse(BaseModel):
    """Full purchase order with items, supplier, and traceability."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(description="PO UUID", example="po1a2b3c-d4e5-6789-abcd-1234567890ab")
    order_number: str = Field(description="Auto-generated order number", example="OC-2026-0001")
    fk_supplier_id: str = Field(description="Supplier UUID")
    supplier: Optional[SupplierEmbedResponse] = Field(None, description="Embedded supplier details")
    order_date: Optional[str] = Field(None, description="Order creation date", example="2026-04-01")
    expected_date: Optional[str] = Field(None, description="Expected delivery date", example="2026-05-01")
    notes: Optional[str] = Field(None, description="Notes", example="Urgente")
    order_status: str = Field(description="Status: draft, sent, partial, received, cancelled", example="draft")
    total_amount: float = Field(0.0, description="Total order amount", example=250.00)
    items: List[PurchaseOrderItemResponse] = Field(default=[], description="Line items")
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    created_by: Optional[str] = Field(None, description="Creator user UUID")
    sent_at: Optional[str] = Field(None, description="Sent timestamp (traceability)")
    sent_by: Optional[str] = Field(None, description="Sent by user UUID")
    received_at: Optional[str] = Field(None, description="Received timestamp")
    received_by: Optional[str] = Field(None, description="Received by user UUID")
