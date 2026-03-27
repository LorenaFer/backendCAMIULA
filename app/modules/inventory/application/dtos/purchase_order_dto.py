"""DTOs del caso de uso de Órdenes de Compra."""

from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional


@dataclass
class PurchaseOrderItemInputDTO:
    medication_id: str
    quantity_ordered: int
    unit_cost: float


@dataclass
class CreatePurchaseOrderDTO:
    fk_supplier_id: str
    items: List[PurchaseOrderItemInputDTO] = field(default_factory=list)
    expected_date: Optional[date] = None
    notes: Optional[str] = None


@dataclass
class ReceivedItemDTO:
    purchase_order_item_id: str
    quantity_received: int
    lot_number: str
    expiration_date: date
    unit_cost: Optional[float] = None


@dataclass
class ReceivePurchaseOrderDTO:
    order_id: str
    items: List[ReceivedItemDTO] = field(default_factory=list)
