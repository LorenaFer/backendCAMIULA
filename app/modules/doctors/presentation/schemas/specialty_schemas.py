"""Pydantic schemas for Specialty resource."""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# --- Input ---


class SpecialtyCreate(BaseModel):
    name: str = Field(..., max_length=200)


class SpecialtyUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)


# --- Output ---


class SpecialtyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    status: Optional[str] = None
    created_at: Optional[str] = None
