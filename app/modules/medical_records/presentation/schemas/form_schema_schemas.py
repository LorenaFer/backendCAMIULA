"""Pydantic schemas for Form Schemas."""

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


# --- Input ---


class FormSchemaUpsert(BaseModel):
    specialty_id: str = Field(..., max_length=36)
    specialty_name: str = Field(..., max_length=200)
    version: str = Field(..., max_length=50)
    schema_json: Optional[Any] = None


# --- Output ---


class FormSchemaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    specialty_id: str
    specialty_name: str
    version: str
    schema_json: Optional[Any] = None
    status: str
    created_at: Optional[str] = None
    created_by: Optional[str] = None
    updated_at: Optional[str] = None
    updated_by: Optional[str] = None
