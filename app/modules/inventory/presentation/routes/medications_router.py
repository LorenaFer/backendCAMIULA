"""FastAPI routes for the Medication resource."""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.modules.inventory.application.dtos.medication_dto import (
    CreateMedicationDTO,
    UpdateMedicationDTO,
)
from app.modules.inventory.application.use_cases.medications.create_medication import (
    CreateMedication,
)
from app.modules.inventory.application.use_cases.medications.get_medication_by_id import (
    GetMedicationById,
)
from app.modules.inventory.application.use_cases.medications.get_medications import (
    GetMedications,
)
from app.modules.inventory.application.use_cases.medications.soft_delete_medication import (
    SoftDeleteMedication,
)
from app.modules.inventory.application.use_cases.medications.update_medication import (
    UpdateMedication,
)
from app.modules.inventory.presentation.dependencies import get_medication_repo
from app.modules.inventory.presentation.schemas.medication_schemas import (
    MedicationCreate,
    MedicationOptionResponse,
    MedicationResponse,
    MedicationUpdate,
)
from app.shared.database.session import get_db
from app.shared.middleware.auth import get_current_user_id, get_optional_user_id
from app.shared.schemas.responses import created, ok, paginated

router = APIRouter(prefix="/medications", tags=["Inventory — Medications"])


@router.get("", summary="List medications")
async def list_medications(
    search: Optional[str] = Query(None, description="Búsqueda por nombre genérico"),
    status: Optional[str] = Query(None, description="Filtrar por medication_status"),
    therapeutic_class: Optional[str] = Query(None),
    category_id: Optional[str] = Query(None, description="Filter by category UUID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_optional_user_id),
):
    """List medications with current stock levels computed from active batches. Supports search, status filter, therapeutic_class, and category_id."""
    repo = get_medication_repo(session)
    items, total = await GetMedications(repo).execute(
        search=search,
        status=status,
        therapeutic_class=therapeutic_class,
        category_id=category_id,
        page=page,
        page_size=page_size,
    )
    data = [MedicationResponse(**m.__dict__) for m in items]
    return paginated(data, total, page, page_size, "Medications retrieved successfully")


@router.get("/options", summary="Simplified list for dropdowns")
async def get_medication_options(
    search: Optional[str] = Query(None, description="Filtrar por nombre genérico"),
    limit: int = Query(100, ge=1, le=500, description="Máximo de resultados"),
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_optional_user_id),
):
    """Simplified medication list for dropdown selects. Only active medications."""
    repo = get_medication_repo(session)
    options = await repo.find_options(search=search, limit=limit)
    data = [MedicationOptionResponse(**m.__dict__) for m in options]
    return ok(data=data, message="Medication options retrieved")


@router.get("/{id}", summary="Medication detail with current stock")
async def get_medication(
    id: str,
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_optional_user_id),
):
    """Retrieve a medication's full details including real-time stock level and category."""
    repo = get_medication_repo(session)
    medication = await GetMedicationById(repo).execute(id)
    if not medication:
        raise NotFoundException("Medication not found.")
    return ok(
        data=MedicationResponse(**medication.__dict__),
        message="Medication retrieved successfully",
    )


@router.post("", summary="Create a new medication", status_code=201)
async def create_medication(
    body: MedicationCreate,
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Register a new medication. The code must be unique. Optionally assign a category."""
    repo = get_medication_repo(session)
    dto = CreateMedicationDTO(**body.model_dump())
    medication = await CreateMedication(repo).execute(dto, created_by=user_id)
    return created(
        data=MedicationResponse(**medication.__dict__),
        message="Medication created successfully",
    )


@router.patch("/{id}", summary="Update medication")
async def update_medication(
    id: str,
    body: MedicationUpdate,
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Update medication catalog fields (PATCH semantics)."""
    repo = get_medication_repo(session)
    dto = UpdateMedicationDTO(**body.model_dump(exclude_none=True))
    medication = await UpdateMedication(repo).execute(id, dto, updated_by=user_id)
    return ok(
        data=MedicationResponse(**medication.__dict__),
        message="Medication updated successfully",
    )


@router.delete("/{id}", summary="Delete medication (soft-delete)")
async def delete_medication(
    id: str,
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Soft-delete a medication from the catalog."""
    repo = get_medication_repo(session)
    await SoftDeleteMedication(repo).execute(id, deleted_by=user_id)
    return ok(message="Medication deleted successfully")
