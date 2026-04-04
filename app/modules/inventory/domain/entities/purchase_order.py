"""Domain entities: Purchase Order and items."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class MedicationEmbed:
    id: str
    code: str
    generic_name: str
    pharmaceutical_form: str
    unit_measure: str


@dataclass
class SupplierEmbed:
    id: str
    name: str
    rif: Optional[str] = None


@dataclass
class PurchaseOrderItem:
    id: str
    fk_purchase_order_id: str
    fk_medication_id: str
    quantity_ordered: int
    quantity_received: int
    item_status: str
    unit_cost: Optional[float] = None
    medication: Optional[MedicationEmbed] = None


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
    total_amount: float = 0.0
    supplier: Optional[SupplierEmbed] = None
    sent_at: Optional[str] = None
    sent_by: Optional[str] = None
    received_at: Optional[str] = None
    received_by: Optional[str] = None
    created_at: Optional[str] = None
    created_by: Optional[str] = None
