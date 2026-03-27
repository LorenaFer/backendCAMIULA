"""DTOs del caso de uso de Lotes."""

from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class CreateBatchDTO:
    fk_medication_id: str
    lot_number: str
    expiration_date: date
    quantity_received: int
    received_at: date
    fk_supplier_id: Optional[str] = None
    fk_purchase_order_id: Optional[str] = None
    unit_cost: Optional[float] = None
