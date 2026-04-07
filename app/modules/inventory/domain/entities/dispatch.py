"""Entidad de dominio: Despacho de farmacia y sus ítems."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class DispatchItem:
    id: str
    fk_dispatch_id: str
    fk_batch_id: str
    fk_medication_id: str
    quantity_dispatched: int


@dataclass
class Dispatch:
    id: str
    fk_prescription_id: str
    fk_patient_id: str
    fk_pharmacist_id: str
    dispatch_date: str
    dispatch_status: str
    items: List[DispatchItem] = field(default_factory=list)
    notes: Optional[str] = None
    created_at: Optional[str] = None
    created_by: Optional[str] = None
    # Enriched display fields (populated in list queries)
    prescription_number: Optional[str] = None
    patient_full_name: Optional[str] = None
    pharmacist_full_name: Optional[str] = None
