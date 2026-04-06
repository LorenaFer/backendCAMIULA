"""Pydantic schemas for Purchase Orders."""

from datetime import date
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ─── Input ────────────────────────────────────────────────────


class PurchaseOrderItemCreate(BaseModel):
    medication_id: str
    quantity_ordered: int = Field(..., ge=1)
    unit_cost: float = Field(..., ge=0)


class PurchaseOrderCreate(BaseModel):
    fk_supplier_id: str
    expected_date: Optional[date] = None
    notes: Optional[str] = Field(None, max_length=500)
    items: List[PurchaseOrderItemCreate] = Field(..., min_length=1)


class PurchaseOrderStatusUpdate(BaseModel):
    order_status: str


class ReceiveItemInput(BaseModel):
    purchase_order_item_id: str
    quantity_received: int = Field(..., ge=1)
    lot_number: str = Field(..., max_length=100)
    expiration_date: date
    unit_cost: Optional[float] = Field(None, ge=0)


class ReceivePurchaseOrderInput(BaseModel):
    items: List[ReceiveItemInput] = Field(..., min_length=1)


# ─── Embedded ─────────────────────────────────────────────────


class SupplierEmbedResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    rif: Optional[str] = None


class MedicationEmbedResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    code: str
    generic_name: str
    pharmaceutical_form: str
    unit_measure: str


# ─── Output ───────────────────────────────────────────────────


class PurchaseOrderItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    fk_medication_id: str
    medication: Optional[MedicationEmbedResponse] = None
    quantity_ordered: int
    quantity_received: int
    unit_cost: Optional[float]
    item_status: str


class PurchaseOrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    order_number: str
    fk_supplier_id: str
    supplier: Optional[SupplierEmbedResponse] = None
    order_date: Optional[str] = None
    expected_date: Optional[str] = None
    notes: Optional[str] = None
    order_status: str
    total_amount: float = 0.0
    items: List[PurchaseOrderItemResponse] = []
    created_at: Optional[str] = None
    created_by: Optional[str] = None
    sent_at: Optional[str] = None
    sent_by: Optional[str] = None
    received_at: Optional[str] = None
    received_by: Optional[str] = None
