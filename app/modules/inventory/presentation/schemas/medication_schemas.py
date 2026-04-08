"""Pydantic schemas for Medications and Categories."""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# ─── Categories ──────────────────────────────────────────────


class MedicationCategoryCreate(BaseModel):
    """Create a medication category."""

    name: str = Field(..., max_length=100, description="Category name (unique)", example="Antibiotico")
    description: Optional[str] = Field(None, max_length=500, description="Category description", example="Medicamentos para combatir infecciones bacterianas")


class MedicationCategoryUpdate(BaseModel):
    """Update a medication category."""

    name: Optional[str] = Field(None, max_length=100, description="New name", example="Antibiotico de amplio espectro")
    description: Optional[str] = Field(None, max_length=500, description="New description")


class MedicationCategoryResponse(BaseModel):
    """Medication category."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(description="Category UUID", example="c1a2b3c4-d5e6-7890-abcd-1234567890ab")
    name: str = Field(description="Category name", example="Antibiotico")
    description: Optional[str] = Field(None, description="Description", example="Medicamentos para combatir infecciones bacterianas")
    created_at: Optional[str] = Field(None, description="Creation timestamp", example="2026-01-01T00:00:00+00:00")


# ─── Medications ─────────────────────────────────────────────


class MedicationCreate(BaseModel):
    """Register a new medication in the catalog."""

    code: str = Field(..., max_length=50, description="Unique medication code", example="MED-001")
    generic_name: str = Field(..., max_length=200, description="Generic (scientific) name", example="Amoxicilina")
    pharmaceutical_form: str = Field(..., max_length=100, description="Form: tablet, capsule, syrup, injection, cream", example="tablet")
    unit_measure: str = Field(..., max_length=50, description="Unit of measure: unit, ml, mg, g", example="unit")
    controlled_substance: bool = Field(description="Requires controlled substance handling", example=False)
    requires_refrigeration: bool = Field(description="Requires cold chain storage", example=False)
    commercial_name: Optional[str] = Field(None, max_length=200, description="Brand/commercial name", example="Amoxil")
    concentration: Optional[str] = Field(None, max_length=100, description="Active ingredient concentration", example="500mg")
    therapeutic_class: Optional[str] = Field(None, max_length=100, description="Therapeutic classification (free text)", example="Antibiotico")
    fk_category_id: Optional[str] = Field(None, description="Category UUID (from /categories)", example="c1a2b3c4-d5e6-7890-abcd-1234567890ab")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "code": "MED-001", "generic_name": "Amoxicilina", "pharmaceutical_form": "tablet",
            "unit_measure": "unit", "controlled_substance": False, "requires_refrigeration": False,
            "commercial_name": "Amoxil", "concentration": "500mg", "therapeutic_class": "Antibiotico",
        }
    })


class MedicationUpdate(BaseModel):
    """Update medication fields (PATCH semantics)."""

    generic_name: Optional[str] = Field(None, max_length=200, description="Generic name", example="Amoxicilina Trihydrate")
    commercial_name: Optional[str] = Field(None, max_length=200, description="Commercial name", example="Amoxil Plus")
    pharmaceutical_form: Optional[str] = Field(None, max_length=100, example="capsule")
    concentration: Optional[str] = Field(None, max_length=100, example="875mg")
    unit_measure: Optional[str] = Field(None, max_length=50, example="unit")
    therapeutic_class: Optional[str] = Field(None, max_length=100, example="Antibiotico")
    fk_category_id: Optional[str] = Field(None, description="Category UUID", example="c1a2b3c4-d5e6-7890-abcd-1234567890ab")
    controlled_substance: Optional[bool] = Field(None, example=False)
    requires_refrigeration: Optional[bool] = Field(None, example=False)
    medication_status: Optional[str] = Field(None, description="Status: active, discontinued, pending", example="active")


class MedicationResponse(BaseModel):
    """Full medication with real-time stock level."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(description="Medication UUID", example="m1e2d3c4-b5a6-7890-abcd-1234567890ab")
    code: str = Field(description="Unique code", example="MED-001")
    generic_name: str = Field(description="Generic name", example="Amoxicilina")
    commercial_name: Optional[str] = Field(None, description="Brand name", example="Amoxil")
    pharmaceutical_form: str = Field(description="Form", example="tablet")
    concentration: Optional[str] = Field(None, description="Concentration", example="500mg")
    unit_measure: str = Field(description="Unit", example="unit")
    therapeutic_class: Optional[str] = Field(None, description="Therapeutic class", example="Antibiotico")
    fk_category_id: Optional[str] = Field(None, description="Category UUID")
    category_name: Optional[str] = Field(None, description="Category name (resolved via JOIN)", example="Antibiotico")
    controlled_substance: bool = Field(description="Controlled substance flag", example=False)
    requires_refrigeration: bool = Field(description="Cold chain flag", example=False)
    medication_status: str = Field(description="Catalog status", example="active")
    current_stock: int = Field(description="Available units (computed from active non-expired batches)", example=350)
    created_at: Optional[str] = Field(None, description="Creation timestamp", example="2026-01-15T10:00:00+00:00")


class MedicationOptionResponse(BaseModel):
    """Lightweight medication for dropdown selects."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(description="Medication UUID", example="m1e2d3c4-b5a6-7890-abcd-1234567890ab")
    code: str = Field(description="Code", example="MED-001")
    generic_name: str = Field(description="Generic name", example="Amoxicilina")
    pharmaceutical_form: str = Field(description="Form", example="tablet")
    unit_measure: str = Field(description="Unit", example="unit")
    current_stock: int = Field(description="Available units", example=350)
