"""FastAPI routes for the Supplier resource."""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, NotFoundException
from app.modules.inventory.presentation.dependencies import get_supplier_repo
from app.modules.inventory.presentation.schemas.supplier_schemas import (
    SupplierCreate,
    SupplierOptionResponse,
    SupplierResponse,
    SupplierUpdate,
)
from app.shared.database.session import get_db
from app.shared.middleware.auth import get_current_user_id
from app.shared.schemas.responses import created, ok, paginated

router = APIRouter(prefix="/suppliers", tags=["Inventory — Suppliers"])


@router.get("", summary="List suppliers (paginated)")
async def list_suppliers(
    search: Optional[str] = Query(None, description="Search by name"),
    status: Optional[str] = Query(None, description="Filter by supplier_status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    repo = get_supplier_repo(session)
    items, total = await repo.find_all(
        search=search,
        status=status,
        page=page,
        page_size=page_size,
    )
    data = [SupplierResponse(**s.__dict__) for s in items]
    return paginated(data, total, page, page_size, "Suppliers retrieved successfully")


@router.get("/options", summary="Active suppliers for select dropdowns")
async def get_supplier_options(
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    repo = get_supplier_repo(session)
    options = await repo.find_options()
    data = [SupplierOptionResponse(**s.__dict__) for s in options]
    return ok(data=data, message="Supplier options retrieved successfully")


@router.get("/{id}", summary="Get supplier by ID")
async def get_supplier(
    id: str,
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    repo = get_supplier_repo(session)
    supplier = await repo.find_by_id(id)
    if not supplier:
        raise NotFoundException("Supplier not found.")
    return ok(
        data=SupplierResponse(**supplier.__dict__),
        message="Supplier retrieved successfully",
    )


@router.post("", summary="Create a new supplier", status_code=201)
async def create_supplier(
    body: SupplierCreate,
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    repo = get_supplier_repo(session)

    existing = await repo.find_by_rif(body.rif)
    if existing:
        raise ConflictException("A supplier with this RIF already exists.")

    data = body.model_dump()
    supplier = await repo.create(data, created_by=user_id)
    return created(
        data=SupplierResponse(**supplier.__dict__),
        message="Supplier created successfully",
    )


@router.patch("/{id}", summary="Update a supplier")
async def update_supplier(
    id: str,
    body: SupplierUpdate,
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    repo = get_supplier_repo(session)

    existing = await repo.find_by_id(id)
    if not existing:
        raise NotFoundException("Supplier not found.")

    data = body.model_dump(exclude_none=True)
    supplier = await repo.update(id, data, updated_by=user_id)
    return ok(
        data=SupplierResponse(**supplier.__dict__),
        message="Supplier updated successfully",
    )
