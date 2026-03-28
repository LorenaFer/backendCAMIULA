"""Entidades de dominio: Orden de compra y sus ítems."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class PurchaseOrderItem:
    id: str
    fk_purchase_order_id: str
    fk_medication_id: str
    quantity_ordered: int
    quantity_received: int
    item_status: str
    unit_cost: Optional[float] = None


@dataclass
class PurchaseOrder:
    id: str
    fk_supplier_id: str
    order_number: str
    order_date: str
    order_status: str
    items: List[PurchaseOrderItem] = field(default_factory=list)
    expected_date: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[str] = None
    created_by: Optional[str] = None
