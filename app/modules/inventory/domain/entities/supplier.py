"""Entidad de dominio: Proveedor."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Supplier:
    id: str
    name: str
    rif: str
    supplier_status: str
    phone: Optional[str] = None
    email: Optional[str] = None
    contact_name: Optional[str] = None
    payment_terms: Optional[str] = None
    created_at: Optional[str] = None
    created_by: Optional[str] = None
