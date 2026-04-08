"""Pydantic schemas for Dynamic Form Schemas."""

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class FormSchemaUpsert(BaseModel):
    """Create or update a form schema for a specialty."""

    specialty_id: str = Field(..., max_length=36, description="Specialty UUID", example="f1e2d3c4-b5a6-7890-abcd-1234567890ab")
    specialty_name: str = Field(..., max_length=200, description="Specialty name (for display)", example="Medicina General")
    version: str = Field(..., max_length=50, description="Schema version", example="1.0")
    schema_json: Optional[Any] = Field(None, description="Form structure: sections with fields (type, label, required)", example={"sections": [{"title": "Motivo de Consulta", "fields": [{"name": "motivo", "type": "textarea", "required": True}]}]})


class FormSchemaResponse(BaseModel):
    """Dynamic form schema for medical record entry."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(description="Schema UUID", example="fs1a2b3c-d4e5-6789-abcd-1234567890ab")
    specialty_id: str = Field(description="Specialty UUID")
    specialty_name: str = Field(description="Specialty name", example="Medicina General")
    version: str = Field(description="Schema version", example="1.0")
    schema_json: Optional[Any] = Field(None, description="Form structure with sections and fields")
    status: str = Field(description="Record status: A (active), T (deleted)", example="A")
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    created_by: Optional[str] = Field(None, description="Creator UUID")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")
    updated_by: Optional[str] = Field(None, description="Last updater UUID")
