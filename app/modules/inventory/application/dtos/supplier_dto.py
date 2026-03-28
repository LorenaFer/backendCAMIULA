"""DTOs del caso de uso de Proveedores."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class CreateSupplierDTO:
    name: str
    rif: str
    phone: Optional[str] = None
    email: Optional[str] = None
    contact_name: Optional[str] = None
    payment_terms: Optional[str] = None


@dataclass
class UpdateSupplierDTO:
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    contact_name: Optional[str] = None
    payment_terms: Optional[str] = None
    supplier_status: Optional[str] = None
