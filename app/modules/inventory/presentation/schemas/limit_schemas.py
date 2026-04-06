"""Pydantic schemas for Dispatch Limits and Exceptions."""

from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class DispatchLimitCreate(BaseModel):
    """Create a monthly dispatch limit for a medication."""

    fk_medication_id: str = Field(description="Medication UUID", example="m1e2d3c4-b5a6-7890-abcd-1234567890ab")
    monthly_max_quantity: int = Field(..., ge=1, description="Maximum units per month", example=60)
    applies_to: str = Field("all", description="Beneficiary type: all, student, employee, professor", example="all")

    model_config = ConfigDict(json_schema_extra={
        "example": {"fk_medication_id": "m1e2d3c4-b5a6-7890-abcd-1234567890ab", "monthly_max_quantity": 60, "applies_to": "all"}
    })


class DispatchLimitUpdate(BaseModel):
    """Update a dispatch limit."""

    monthly_max_quantity: Optional[int] = Field(None, ge=1, description="New monthly max", example=90)
    applies_to: Optional[str] = Field(None, description="New beneficiary type", example="student")
    active: Optional[bool] = Field(None, description="Enable/disable the limit", example=True)


class DispatchLimitResponse(BaseModel):
    """Monthly dispatch limit configuration."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(description="Limit UUID", example="l1a2b3c4-d5e6-7890-abcd-1234567890ab")
    fk_medication_id: str = Field(description="Medication UUID")
    monthly_max_quantity: int = Field(description="Max units per month", example=60)
    applies_to: str = Field(description="Beneficiary type", example="all")
    active: bool = Field(description="Whether limit is active", example=True)
    created_at: Optional[str] = Field(None, description="Creation timestamp")


class DispatchExceptionCreate(BaseModel):
    """Authorize a patient to exceed the monthly limit."""

    fk_patient_id: str = Field(description="Patient UUID", example="a1b2c3d4-e5f6-7890-abcd-1234567890ab")
    fk_medication_id: str = Field(description="Medication UUID", example="m1e2d3c4-b5a6-7890-abcd-1234567890ab")
    authorized_quantity: int = Field(..., ge=1, description="Authorized quantity (overrides limit)", example=120)
    valid_from: date = Field(description="Exception start date", example="2026-04-01")
    valid_until: date = Field(description="Exception end date", example="2026-06-30")
    reason: str = Field(..., max_length=500, description="Medical justification", example="Tratamiento cronico autorizado por jefatura")
    authorized_by: Optional[str] = Field(None, max_length=200, description="Authorizing person name", example="Dra. Ana Lopez")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "fk_patient_id": "a1b2c3d4-e5f6-7890-abcd-1234567890ab",
            "fk_medication_id": "m1e2d3c4-b5a6-7890-abcd-1234567890ab",
            "authorized_quantity": 120, "valid_from": "2026-04-01", "valid_until": "2026-06-30",
            "reason": "Tratamiento cronico autorizado por jefatura", "authorized_by": "Dra. Ana Lopez",
        }
    })


class DispatchExceptionResponse(BaseModel):
    """Authorized exception to a dispatch limit."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(description="Exception UUID")
    fk_patient_id: str = Field(description="Patient UUID")
    fk_medication_id: str = Field(description="Medication UUID")
    authorized_quantity: int = Field(description="Authorized quantity", example=120)
    valid_from: str = Field(description="Start date", example="2026-04-01")
    valid_until: str = Field(description="End date", example="2026-06-30")
    reason: str = Field(description="Justification", example="Tratamiento cronico")
    authorized_by: Optional[str] = Field(None, description="Authorizing person", example="Dra. Ana Lopez")
    created_at: Optional[str] = Field(None, description="Creation timestamp")
