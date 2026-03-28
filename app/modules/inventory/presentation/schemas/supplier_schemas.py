"""Schemas Pydantic para el recurso Proveedor.

Alineados con la interfaz Supplier de inventory.ts.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class SupplierCreate(BaseModel):
    name: str = Field(..., max_length=200)
    rif: str = Field(..., max_length=20)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=200)
    contact_name: Optional[str] = Field(None, max_length=200)
    payment_terms: Optional[str] = Field(None, max_length=500)


class SupplierUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=200)
    contact_name: Optional[str] = Field(None, max_length=200)
    payment_terms: Optional[str] = Field(None, max_length=500)
    supplier_status: Optional[str] = None


class SupplierResponse(BaseModel):
    """Espejo de la interfaz Supplier del frontend."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    rif: str
    phone: Optional[str]
    email: Optional[str]
    contact_name: Optional[str]
    payment_terms: Optional[str]
    supplier_status: str
    created_at: Optional[str]


class SupplierOptionResponse(BaseModel):
    """Espejo de la interfaz SupplierOption del frontend."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    rif: str
