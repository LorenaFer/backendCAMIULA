"""Entidad de dominio: Medicamento."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Medication:
    id: str
    code: str
    generic_name: str
    pharmaceutical_form: str
    unit_measure: str
    controlled_substance: bool
    requires_refrigeration: bool
    medication_status: str
    commercial_name: Optional[str] = None
    concentration: Optional[str] = None
    therapeutic_class: Optional[str] = None
    fk_category_id: Optional[str] = None
    category_name: Optional[str] = None
    current_stock: int = 0
    created_at: Optional[str] = None
    created_by: Optional[str] = None
