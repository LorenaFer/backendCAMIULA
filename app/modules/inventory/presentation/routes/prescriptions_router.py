"""FastAPI routes for the Prescription resource."""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.modules.inventory.infrastructure.repositories.sqlalchemy_prescription_repository import (
    SQLAlchemyPrescriptionRepository,
)
from app.modules.inventory.presentation.schemas.prescription_schemas import (
    PrescriptionCreate,
    PrescriptionResponse,
)
from app.shared.database.session import get_db
from app.shared.middleware.auth import get_current_user_id
from app.shared.schemas.responses import created, ok, paginated

router = APIRouter(prefix="/prescriptions", tags=["Inventory — Prescriptions"])


@router.get("", summary="List / search prescriptions")
async def list_prescriptions(
    appointment_id: Optional[str] = Query(None, description="Filter by appointment ID"),
    prescription_number: Optional[str] = Query(None, description="Filter by prescription number"),
    patient_id: Optional[str] = Query(None, description="Filter by patient ID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    repo = SQLAlchemyPrescriptionRepository(session)

    # Single-result lookups
    if appointment_id:
        prescription = await repo.find_by_appointment(appointment_id)
        if not prescription:
            raise NotFoundException("Prescription not found for this appointment.")
        return ok(
            data=PrescriptionResponse(**prescription.__dict__),
            message="Prescription retrieved successfully",
        )

    if prescription_number:
        prescription = await repo.find_by_number(prescription_number)
        if not prescription:
            raise NotFoundException("Prescription not found.")
        return ok(
            data=PrescriptionResponse(**prescription.__dict__),
            message="Prescription retrieved successfully",
        )

    # Paginated list by patient
    if patient_id:
        items, total = await repo.find_by_patient(patient_id, page, page_size)
        data = [PrescriptionResponse(**p.__dict__) for p in items]
        return paginated(data, total, page, page_size, "Prescriptions retrieved successfully")

    # No filter provided — return empty guidance
    return ok(data=[], message="Provide appointment_id, prescription_number, or patient_id to search")


@router.get("/{id}", summary="Get prescription by ID")
async def get_prescription(
    id: str,
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    repo = SQLAlchemyPrescriptionRepository(session)
    prescription = await repo.find_by_id(id)
    if not prescription:
        raise NotFoundException("Prescription not found.")
    return ok(
        data=PrescriptionResponse(**prescription.__dict__),
        message="Prescription retrieved successfully",
    )


@router.post("", summary="Create a new prescription", status_code=201)
async def create_prescription(
    body: PrescriptionCreate,
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    repo = SQLAlchemyPrescriptionRepository(session)

    # Build the data dict expected by the repository
    prescription_number = await repo.get_next_number()
    data = body.model_dump()

    # Rename item fields to match repository expectations
    items_raw = data.pop("items", [])
    items = []
    for item in items_raw:
        items.append({
            "fk_medication_id": item["medication_id"],
            "quantity_prescribed": item["quantity_prescribed"],
            "dosage_instructions": item.get("dosage_instructions"),
            "duration_days": item.get("duration_days"),
        })
    data["items"] = items
    data["prescription_number"] = prescription_number
    data["prescription_date"] = date.today().isoformat()
    data["prescription_status"] = "issued"

    prescription = await repo.create(data, created_by=user_id)
    return created(
        data=PrescriptionResponse(**prescription.__dict__),
        message="Prescription created successfully",
    )
