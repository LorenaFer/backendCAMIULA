"""Entidades de dominio: Límite de despacho y excepción autorizada."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class DispatchLimit:
    id: str
    fk_medication_id: str
    monthly_max_quantity: int
    applies_to: str
    active: bool
    created_at: Optional[str] = None
    created_by: Optional[str] = None


@dataclass
class DispatchException:
    id: str
    fk_patient_id: str
    fk_medication_id: str
    authorized_quantity: int
    valid_from: str
    valid_until: str
    reason: str
    authorized_by: Optional[str] = None
    created_at: Optional[str] = None
    created_by: Optional[str] = None
