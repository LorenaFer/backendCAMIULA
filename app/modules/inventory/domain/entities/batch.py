"""Entidad de dominio: Lote de medicamento."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Batch:
    id: str
    fk_medication_id: str
    lot_number: str
    expiration_date: str
    quantity_received: int
    quantity_available: int
    received_at: str
    batch_status: str
    fk_supplier_id: Optional[str] = None
    fk_purchase_order_id: Optional[str] = None
    unit_cost: Optional[float] = None
    created_at: Optional[str] = None
    created_by: Optional[str] = None
