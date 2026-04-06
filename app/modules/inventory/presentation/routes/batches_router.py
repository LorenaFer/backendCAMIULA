"""FastAPI routes for the Batch resource."""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.modules.inventory.infrastructure.repositories.sqlalchemy_batch_repository import (
    SQLAlchemyBatchRepository,
)
from app.modules.inventory.presentation.schemas.batch_schemas import (
    BatchResponse,
)
from app.shared.database.session import get_db
from app.shared.middleware.auth import get_current_user_id
from app.shared.schemas.responses import ok, paginated

router = APIRouter(prefix="/batches", tags=["Inventory — Batches"])


@router.get("", summary="List batches with filters (paginated)")
async def list_batches(
    medication_id: Optional[str] = Query(None, description="Filter by medication ID"),
    status: Optional[str] = Query(None, description="Filter by batch_status"),
    expiring_before: Optional[str] = Query(
        None, description="ISO date YYYY-MM-DD — batches expiring on or before this date"
    ),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    repo = SQLAlchemyBatchRepository(session)
    items, total = await repo.find_all(
        medication_id=medication_id,
        status=status,
        expiring_before=expiring_before,
        page=page,
        page_size=page_size,
    )
    data = [BatchResponse(**b.__dict__) for b in items]
    return paginated(data, total, page, page_size, "Batches retrieved successfully")


@router.get("/{id}", summary="Get batch by ID")
async def get_batch(
    id: str,
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    repo = SQLAlchemyBatchRepository(session)
    batch = await repo.find_by_id(id)
    if not batch:
        raise NotFoundException("Batch not found.")
    return ok(
        data=BatchResponse(**batch.__dict__),
        message="Batch retrieved successfully",
    )
