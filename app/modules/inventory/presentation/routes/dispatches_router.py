"""FastAPI routes for the Dispatch resource."""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.modules.inventory.application.use_cases.dispatches.cancel_dispatch import (
    cancel_dispatch,
)
from app.modules.inventory.application.use_cases.dispatches.execute_dispatch import (
    execute_dispatch,
)
from app.modules.inventory.application.use_cases.dispatches.validate_and_prepare_dispatch import (
    validate_and_prepare_dispatch,
)
from app.modules.inventory.presentation.dependencies import (
    get_batch_repo, get_dispatch_repo, get_movement_repo,
)
from app.modules.inventory.presentation.dependencies import (
    get_limit_repo, get_medication_repo, get_prescription_repo,
)
from app.modules.inventory.presentation.schemas.dispatch_schemas import (
    DispatchCreate,
    DispatchResponse,
    DispatchValidationResponse,
)
from app.shared.database.session import get_db
from app.shared.middleware.auth import get_current_user_id, get_optional_user_id
from app.shared.schemas.responses import created, ok, paginated

router = APIRouter(prefix="/dispatches", tags=["Inventory — Dispatches"])


# ──────────────────────────────────────────────────────────
# List dispatches (paginated)
# ──────────────────────────────────────────────────────────


@router.get("", summary="List dispatches (paginated, filterable)")
async def list_dispatches(
    patient_id: Optional[str] = Query(None, description="Filter by patient ID"),
    prescription_number: Optional[str] = Query(None, description="Search by prescription number"),
    status: Optional[str] = Query(None, description="Filter by dispatch_status"),
    date_from: Optional[str] = Query(None, description="Start date YYYY-MM-DD"),
    date_to: Optional[str] = Query(None, description="End date YYYY-MM-DD"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=10000),
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_optional_user_id),
):
    """List pharmacy dispatches with filters: patient_id, prescription_number, status, date range."""
    repo = get_dispatch_repo(session)
    items, total = await repo.find_all(
        patient_id=patient_id,
        prescription_number=prescription_number,
        status=status,
        date_from=date_from,
        date_to=date_to,
        page=page,
        page_size=page_size,
    )
    from app.modules.inventory.presentation.schemas.dispatch_schemas import (
        DispatchResponse,
    )

    data = [DispatchResponse(**d.__dict__) for d in items]
    return paginated(data, total, page, page_size, "Dispatches retrieved successfully")


# ──────────────────────────────────────────────────────────
# Validación previa
# ──────────────────────────────────────────────────────────

@router.get("/validate", summary="Validar despacho (FEFO + límites mensuales)")
async def validate_dispatch(
    prescription_id: str = Query(..., description="ID de la receta a validar"),
    patient_type: str = Query("all", description="Tipo de beneficiario"),
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Pre-validate a dispatch. Checks stock (FEFO), monthly limits, and returns a detailed allocation plan."""
    result = await validate_and_prepare_dispatch(
        prescription_id=prescription_id,
        patient_type=patient_type,
        prescription_repo=get_prescription_repo(session),
        batch_repo=get_batch_repo(session),
        dispatch_repo=get_dispatch_repo(session),
        limit_repo=get_limit_repo(session),
        medication_repo=get_medication_repo(session),
    )
    return ok(
        data=DispatchValidationResponse(**result.__dict__),
        message="Validación completada",
    )


# ──────────────────────────────────────────────────────────
# Ejecución
# ──────────────────────────────────────────────────────────

@router.post("", summary="Ejecutar despacho (FEFO atómico)", status_code=201)
async def create_dispatch(
    body: DispatchCreate,
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Execute a pharmacy dispatch using FEFO. Atomic: validates, allocates stock, checks limits, creates records, updates batches, records movements."""
    dispatch = await execute_dispatch(
        fk_prescription_id=body.fk_prescription_id,
        fk_pharmacist_id=user_id,
        patient_type=body.patient_type,
        notes=body.notes,
        pharmacist_id=user_id,
        prescription_repo=get_prescription_repo(session),
        batch_repo=get_batch_repo(session),
        dispatch_repo=get_dispatch_repo(session),
        limit_repo=get_limit_repo(session),
    )

    # Record exit movements for traceability
    from datetime import datetime, timezone
    movement_repo = get_movement_repo(session)
    for item in dispatch.items:
        balance = await movement_repo.get_current_balance(item.fk_medication_id)
        await movement_repo.record_movement(
            fk_medication_id=item.fk_medication_id,
            movement_type="exit",
            quantity=-item.quantity_dispatched,
            balance_after=balance,
            movement_date=datetime.now(timezone.utc),
            created_by=user_id,
            fk_batch_id=item.fk_batch_id,
            fk_dispatch_id=dispatch.id,
            reference=f"Dispatch {dispatch.id[:8]}",
            notes=body.notes,
        )

    return created(
        data=DispatchResponse(**dispatch.__dict__),
        message="Dispatch executed successfully",
    )


# ──────────────────────────────────────────────────────────
# Consultas
# ──────────────────────────────────────────────────────────

@router.get("/by-prescription/{prescription_id}", summary="Dispatches for a prescription")
async def get_by_prescription(
    prescription_id: str,
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """List all dispatches associated with a prescription."""
    repo = get_dispatch_repo(session)
    dispatches = await repo.find_by_prescription(prescription_id)
    data = [DispatchResponse(**d.__dict__) for d in dispatches]
    return ok(data=data, message="Dispatches retrieved successfully")


@router.get("/by-patient/{patient_id}", summary="Dispatch history for a patient")
async def get_by_patient(
    patient_id: str,
    prescription_number: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None, description="ISO date YYYY-MM-DD"),
    date_to: Optional[str] = Query(None, description="ISO date YYYY-MM-DD"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Paginated dispatch history for a patient."""
    repo = get_dispatch_repo(session)
    dispatches, total = await repo.find_by_patient(
        fk_patient_id=patient_id,
        prescription_number=prescription_number,
        status=status,
        date_from=date_from,
        date_to=date_to,
        page=page,
        page_size=page_size,
    )
    data = [DispatchResponse(**d.__dict__) for d in dispatches]
    return paginated(data, total, page, page_size, "Dispatch history retrieved")


@router.get("/{id}", summary="Dispatch detail")
async def get_dispatch(
    id: str,
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Retrieve a dispatch with item details and batch allocation."""
    repo = get_dispatch_repo(session)
    dispatch = await repo.find_by_id(id)
    if not dispatch:
        raise NotFoundException("Dispatch not found")
    return ok(
        data=DispatchResponse(**dispatch.__dict__),
        message="Dispatch retrieved successfully",
    )


# ──────────────────────────────────────────────────────────
# Cancelación
# ──────────────────────────────────────────────────────────

@router.post("/{id}/cancel", summary="Cancel a dispatch and revert stock")
async def cancel_dispatch_endpoint(
    id: str,
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Cancel a dispatch and revert stock to original batches."""
    await cancel_dispatch(
        dispatch_id=id,
        cancelled_by=user_id,
        dispatch_repo=get_dispatch_repo(session),
        batch_repo=get_batch_repo(session),
        prescription_repo=get_prescription_repo(session),
    )
    return ok(message="Dispatch cancelled and stock reverted successfully")
