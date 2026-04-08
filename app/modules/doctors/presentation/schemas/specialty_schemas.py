"""Pydantic schemas for the Specialty resource."""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class SpecialtyCreate(BaseModel):
    """Create a new medical specialty."""

    name: str = Field(..., max_length=200, description="Specialty name (unique)", example="Cardiologia")


class SpecialtyUpdate(BaseModel):
    """Update an existing specialty."""

    name: Optional[str] = Field(None, max_length=200, description="New specialty name", example="Cardiologia Clinica")


class SpecialtyResponse(BaseModel):
    """Medical specialty."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(description="Specialty UUID", example="f1e2d3c4-b5a6-7890-abcd-1234567890ab")
    name: str = Field(description="Specialty name", example="Medicina General")
    status: Optional[str] = Field(None, description="Record status: A (active), I (inactive)", example="A")
    created_at: Optional[str] = Field(None, description="Creation timestamp", example="2026-01-01T00:00:00+00:00")
