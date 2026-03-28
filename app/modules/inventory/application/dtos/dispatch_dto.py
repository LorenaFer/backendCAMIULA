"""DTOs del caso de uso de Despachos."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class CreateDispatchDTO:
    fk_prescription_id: str
    fk_pharmacist_id: str
    notes: Optional[str] = None


@dataclass
class DispatchValidationItemDTO:
    medication_id: str
    generic_name: str
    quantity_prescribed: int
    quantity_available: int
    monthly_limit: Optional[int]
    monthly_used: int
    monthly_remaining: int
    has_exception: bool
    can_dispatch: bool
    block_reason: Optional[str]


@dataclass
class DispatchValidationDTO:
    can_dispatch: bool
    prescription_id: str
    patient_id: str
    items: List[DispatchValidationItemDTO] = field(default_factory=list)
