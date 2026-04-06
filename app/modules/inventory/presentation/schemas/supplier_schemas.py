"""Pydantic schemas for the Supplier resource."""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class SupplierCreate(BaseModel):
    """Register a new supplier."""

    name: str = Field(..., max_length=200, description="Supplier company name", example="Distribuidora Farmaceutica Nacional")
    rif: str = Field(..., max_length=20, description="RIF (unique tax ID)", example="J-12345678-9")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number", example="0212-1234567")
    email: Optional[str] = Field(None, max_length=200, description="Contact email", example="ventas@dfn.com.ve")
    contact_name: Optional[str] = Field(None, max_length=200, description="Contact person name", example="Roberto Diaz")
    payment_terms: Optional[str] = Field(None, max_length=500, description="Payment terms/conditions", example="Net 30 dias")

    model_config = ConfigDict(json_schema_extra={
        "example": {"name": "Distribuidora Farmaceutica Nacional", "rif": "J-12345678-9", "phone": "0212-1234567", "email": "ventas@dfn.com.ve", "contact_name": "Roberto Diaz", "payment_terms": "Net 30 dias"}
    })


class SupplierUpdate(BaseModel):
    """Update supplier fields."""

    name: Optional[str] = Field(None, max_length=200, description="Company name")
    phone: Optional[str] = Field(None, max_length=20, description="Phone")
    email: Optional[str] = Field(None, max_length=200, description="Email")
    contact_name: Optional[str] = Field(None, max_length=200, description="Contact person")
    payment_terms: Optional[str] = Field(None, max_length=500, description="Payment terms")
    supplier_status: Optional[str] = Field(None, description="Status: active or inactive", example="active")


class SupplierResponse(BaseModel):
    """Full supplier profile."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(description="Supplier UUID", example="s1e2d3c4-b5a6-7890-abcd-1234567890ab")
    name: str = Field(description="Company name", example="Distribuidora Farmaceutica Nacional")
    rif: str = Field(description="RIF (tax ID)", example="J-12345678-9")
    phone: Optional[str] = Field(None, description="Phone", example="0212-1234567")
    email: Optional[str] = Field(None, description="Email", example="ventas@dfn.com.ve")
    contact_name: Optional[str] = Field(None, description="Contact person", example="Roberto Diaz")
    payment_terms: Optional[str] = Field(None, description="Payment terms", example="Net 30 dias")
    supplier_status: str = Field(description="Status: active or inactive", example="active")
    created_at: Optional[str] = Field(None, description="Creation timestamp", example="2026-01-01T00:00:00+00:00")


class SupplierOptionResponse(BaseModel):
    """Lightweight supplier for dropdown selects."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(description="Supplier UUID", example="s1e2d3c4-b5a6-7890-abcd-1234567890ab")
    name: str = Field(description="Company name", example="Distribuidora Farmaceutica Nacional")
    rif: str = Field(description="RIF", example="J-12345678-9")
