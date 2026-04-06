"""FastAPI routes for Dispatch Limits and Dispatch Exceptions."""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.modules.inventory.presentation.dependencies import get_limit_repo
from app.modules.inventory.presentation.schemas.limit_schemas import (
    DispatchExceptionCreate,
    DispatchExceptionResponse,
    DispatchLimitCreate,
    DispatchLimitResponse,
    DispatchLimitUpdate,
)
from app.shared.database.session import get_db
from app.shared.middleware.auth import get_current_user_id
from app.shared.schemas.responses import created, ok, paginated

router = APIRouter(prefix="/dispatch-limits", tags=["Inventory — Dispatch Limits"])

# Secondary router for exceptions under a different prefix
exceptions_router = APIRouter(
    prefix="/dispatch-exceptions", tags=["Inventory — Dispatch Exceptions"]
)


# ------------------------------------------------------------------
# Dispatch Limits
# ------------------------------------------------------------------


@router.get("", summary="List dispatch limits (paginated)")
async def list_limits(
    medication_id: Optional[str] = Query(None, description="Filter by medication ID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    repo = get_limit_repo(session)
    items, total = await repo.find_all_limits(
        medication_id=medication_id,
        page=page,
        page_size=page_size,
    )
    data = [DispatchLimitResponse(**lim.__dict__) for lim in items]
    return paginated(data, total, page, page_size, "Dispatch limits retrieved successfully")


@router.post("", summary="Create a dispatch limit", status_code=201)
async def create_limit(
    body: DispatchLimitCreate,
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    repo = get_limit_repo(session)
    data = body.model_dump()
    limit = await repo.create_limit(data, created_by=user_id)
    return created(
        data=DispatchLimitResponse(**limit.__dict__),
        message="Dispatch limit created successfully",
    )


@router.patch("/{id}", summary="Update a dispatch limit")
async def update_limit(
    id: str,
    body: DispatchLimitUpdate,
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    repo = get_limit_repo(session)

    existing = await repo.find_limit_by_id(id)
    if not existing:
        raise NotFoundException("Dispatch limit not found.")

    data = body.model_dump(exclude_none=True)
    limit = await repo.update_limit(id, data, updated_by=user_id)
    return ok(
        data=DispatchLimitResponse(**limit.__dict__),
        message="Dispatch limit updated successfully",
    )


# ------------------------------------------------------------------
# Dispatch Exceptions
# ------------------------------------------------------------------


@exceptions_router.get("", summary="List dispatch exceptions (paginated)")
async def list_exceptions(
    patient_id: Optional[str] = Query(None, description="Filter by patient ID"),
    medication_id: Optional[str] = Query(None, description="Filter by medication ID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    repo = get_limit_repo(session)
    items, total = await repo.find_all_exceptions(
        patient_id=patient_id,
        medication_id=medication_id,
        page=page,
        page_size=page_size,
    )
    data = [DispatchExceptionResponse(**exc.__dict__) for exc in items]
    return paginated(data, total, page, page_size, "Dispatch exceptions retrieved successfully")


@exceptions_router.post("", summary="Create a dispatch exception", status_code=201)
async def create_exception(
    body: DispatchExceptionCreate,
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    repo = get_limit_repo(session)
    data = body.model_dump()
    # Convert date objects to ISO strings for the model
    if hasattr(data.get("valid_from", None), "isoformat"):
        data["valid_from"] = data["valid_from"]
    if hasattr(data.get("valid_until", None), "isoformat"):
        data["valid_until"] = data["valid_until"]
    exception = await repo.create_exception(data, created_by=user_id)
    return created(
        data=DispatchExceptionResponse(**exception.__dict__),
        message="Dispatch exception created successfully",
    )
