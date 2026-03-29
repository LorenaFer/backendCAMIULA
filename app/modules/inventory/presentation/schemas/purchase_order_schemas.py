"""Schemas Pydantic para el recurso Orden de Compra.

Alineados con las interfaces PurchaseOrder / PurchaseOrderItem de inventory.ts.
"""

from datetime import date
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


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


class PurchaseOrderItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    fk_medication_id: str
    quantity_ordered: int
    quantity_received: int
    unit_cost: Optional[float]
    item_status: str


class PurchaseOrderResponse(BaseModel):
    """Espejo de la interfaz PurchaseOrder del frontend."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    order_number: str
    fk_supplier_id: str
    order_date: str
    expected_date: Optional[str]
    notes: Optional[str]
    order_status: str
    items: List[PurchaseOrderItemResponse]
    created_at: Optional[str]
