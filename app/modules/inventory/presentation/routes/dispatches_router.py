"""Rutas FastAPI para el recurso Despacho (Dispatch)."""

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
from app.modules.inventory.infrastructure.repositories.sqlalchemy_batch_repository import (
    SQLAlchemyBatchRepository,
)
from app.modules.inventory.infrastructure.repositories.sqlalchemy_dispatch_repository import (
    SQLAlchemyDispatchRepository,
)
from app.modules.inventory.infrastructure.repositories.sqlalchemy_limit_repository import (
    SQLAlchemyLimitRepository,
)
from app.modules.inventory.infrastructure.repositories.sqlalchemy_medication_repository import (
    SQLAlchemyMedicationRepository,
)
from app.modules.inventory.infrastructure.repositories.sqlalchemy_prescription_repository import (
    SQLAlchemyPrescriptionRepository,
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
    repo = SQLAlchemyDispatchRepository(session)
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
    result = await validate_and_prepare_dispatch(
        prescription_id=prescription_id,
        patient_type=patient_type,
        prescription_repo=SQLAlchemyPrescriptionRepository(session),
        batch_repo=SQLAlchemyBatchRepository(session),
        dispatch_repo=SQLAlchemyDispatchRepository(session),
        limit_repo=SQLAlchemyLimitRepository(session),
        medication_repo=SQLAlchemyMedicationRepository(session),
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
    dispatch = await execute_dispatch(
        fk_prescription_id=body.fk_prescription_id,
        fk_pharmacist_id=user_id,
        patient_type=body.patient_type,
        notes=body.notes,
        pharmacist_id=user_id,
        prescription_repo=SQLAlchemyPrescriptionRepository(session),
        batch_repo=SQLAlchemyBatchRepository(session),
        dispatch_repo=SQLAlchemyDispatchRepository(session),
        limit_repo=SQLAlchemyLimitRepository(session),
    )
    return created(
        data=DispatchResponse(**dispatch.__dict__),
        message="Despacho ejecutado exitosamente",
    )


# ──────────────────────────────────────────────────────────
# Consultas
# ──────────────────────────────────────────────────────────

@router.get("/by-prescription/{prescription_id}", summary="Despachos de una receta")
async def get_by_prescription(
    prescription_id: str,
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    repo = SQLAlchemyDispatchRepository(session)
    dispatches = await repo.find_by_prescription(prescription_id)
    data = [DispatchResponse(**d.__dict__) for d in dispatches]
    return ok(data=data, message="Despachos obtenidos exitosamente")


@router.get("/by-patient/{patient_id}", summary="Historial de despachos de un paciente")
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
    repo = SQLAlchemyDispatchRepository(session)
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
    return paginated(data, total, page, page_size, "Historial de despachos obtenido")


@router.get("/{id}", summary="Detalle de un despacho")
async def get_dispatch(
    id: str,
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    repo = SQLAlchemyDispatchRepository(session)
    dispatch = await repo.find_by_id(id)
    if not dispatch:
        raise NotFoundException("Despacho no encontrado")
    return ok(
        data=DispatchResponse(**dispatch.__dict__),
        message="Despacho obtenido exitosamente",
    )


# ──────────────────────────────────────────────────────────
# Cancelación
# ──────────────────────────────────────────────────────────

@router.post("/{id}/cancel", summary="Cancelar un despacho y revertir stock")
async def cancel_dispatch_endpoint(
    id: str,
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    await cancel_dispatch(
        dispatch_id=id,
        cancelled_by=user_id,
        dispatch_repo=SQLAlchemyDispatchRepository(session),
        batch_repo=SQLAlchemyBatchRepository(session),
        prescription_repo=SQLAlchemyPrescriptionRepository(session),
    )
    return ok(message="Despacho cancelado y stock revertido exitosamente")
