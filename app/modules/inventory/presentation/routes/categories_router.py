"""FastAPI routes for Medication Categories CRUD."""

from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select, update as sql_update
from sqlalchemy.ext.asyncio import AsyncSession

from datetime import datetime, timezone

from app.core.exceptions import ConflictException, NotFoundException
from app.modules.inventory.infrastructure.models import MedicationCategoryModel
from app.modules.inventory.presentation.schemas.medication_schemas import (
    MedicationCategoryCreate,
    MedicationCategoryResponse,
    MedicationCategoryUpdate,
)
from app.shared.database.mixins import RecordStatus
from app.shared.database.session import get_db
from app.shared.middleware.auth import get_current_user_id, get_optional_user_id
from app.shared.schemas.responses import created, ok, paginated

router = APIRouter(prefix="/categories", tags=["Inventory - Medication Categories"])


@router.get("", summary="List medication categories")
async def list_categories(
    search: Optional[str] = Query(None, description="Search by name"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    session: AsyncSession = Depends(get_db),
    _user_id: str = Depends(get_optional_user_id),
):
    q = select(MedicationCategoryModel).where(
        MedicationCategoryModel.status == RecordStatus.ACTIVE
    )
    if search:
        q = q.where(MedicationCategoryModel.name.ilike(f"%{search}%"))

    total = (
        await session.execute(select(func.count()).select_from(q.subquery()))
    ).scalar_one()

    offset = (page - 1) * page_size
    result = await session.execute(
        q.order_by(MedicationCategoryModel.name).offset(offset).limit(page_size)
    )
    items = [
        MedicationCategoryResponse(
            id=m.id,
            name=m.name,
            description=m.description,
            created_at=m.created_at.isoformat() if m.created_at else None,
        )
        for m in result.scalars().all()
    ]
    return paginated(items, total, page, page_size, "Categories retrieved")


@router.get("/{category_id}", summary="Get category by ID")
async def get_category(
    category_id: str,
    session: AsyncSession = Depends(get_db),
    _user_id: str = Depends(get_optional_user_id),
):
    result = await session.execute(
        select(MedicationCategoryModel).where(
            MedicationCategoryModel.id == category_id,
            MedicationCategoryModel.status == RecordStatus.ACTIVE,
        )
    )
    m = result.scalar_one_or_none()
    if not m:
        raise NotFoundException("Category not found")
    return ok(
        data=MedicationCategoryResponse(
            id=m.id,
            name=m.name,
            description=m.description,
            created_at=m.created_at.isoformat() if m.created_at else None,
        ),
        message="Category retrieved",
    )


@router.post("", summary="Create medication category", status_code=201)
async def create_category(
    body: MedicationCategoryCreate,
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    # Check unique name
    existing = await session.execute(
        select(MedicationCategoryModel).where(
            MedicationCategoryModel.name == body.name,
            MedicationCategoryModel.status == RecordStatus.ACTIVE,
        )
    )
    if existing.scalar_one_or_none():
        raise ConflictException(f"Category '{body.name}' already exists")

    model = MedicationCategoryModel(
        id=str(uuid4()),
        name=body.name,
        description=body.description,
        created_by=user_id,
    )
    session.add(model)
    await session.flush()
    await session.refresh(model)
    return created(
        data=MedicationCategoryResponse(
            id=model.id,
            name=model.name,
            description=model.description,
            created_at=model.created_at.isoformat() if model.created_at else None,
        ),
        message="Category created",
    )


@router.patch("/{category_id}", summary="Update medication category")
async def update_category(
    category_id: str,
    body: MedicationCategoryUpdate,
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    result = await session.execute(
        select(MedicationCategoryModel).where(
            MedicationCategoryModel.id == category_id,
            MedicationCategoryModel.status == RecordStatus.ACTIVE,
        )
    )
    if not result.scalar_one_or_none():
        raise NotFoundException("Category not found")

    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise NotFoundException("No fields to update")

    updates["updated_at"] = datetime.now(timezone.utc)
    updates["updated_by"] = user_id

    await session.execute(
        sql_update(MedicationCategoryModel)
        .where(MedicationCategoryModel.id == category_id)
        .values(**updates)
    )
    await session.flush()

    # Re-fetch
    result = await session.execute(
        select(MedicationCategoryModel).where(
            MedicationCategoryModel.id == category_id,
        )
    )
    m = result.scalar_one()
    return ok(
        data=MedicationCategoryResponse(
            id=m.id,
            name=m.name,
            description=m.description,
            created_at=m.created_at.isoformat() if m.created_at else None,
        ),
        message="Category updated",
    )


@router.delete("/{category_id}", summary="Delete category (soft-delete)")
async def delete_category(
    category_id: str,
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    result = await session.execute(
        select(MedicationCategoryModel).where(
            MedicationCategoryModel.id == category_id,
            MedicationCategoryModel.status == RecordStatus.ACTIVE,
        )
    )
    if not result.scalar_one_or_none():
        raise NotFoundException("Category not found")

    await session.execute(
        sql_update(MedicationCategoryModel)
        .where(MedicationCategoryModel.id == category_id)
        .values(
            status=RecordStatus.TRASH,
            deleted_at=datetime.now(timezone.utc),
            deleted_by=user_id,
        )
    )
    return ok(message="Category deleted")
