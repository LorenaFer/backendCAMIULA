"""FastAPI routes for Medication Categories CRUD.

All DB access goes through CategoryRepository (injected via dependencies.py).
No direct SQLAlchemy imports in this file.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.core.exceptions import ConflictException, NotFoundException
from app.modules.inventory.domain.repositories.category_repository import (
    CategoryRepository,
)
from app.modules.inventory.presentation.dependencies import get_category_repo
from app.modules.inventory.presentation.schemas.medication_schemas import (
    MedicationCategoryCreate,
    MedicationCategoryResponse,
    MedicationCategoryUpdate,
)
from app.shared.middleware.auth import get_current_user_id, get_optional_user_id
from app.shared.schemas.responses import created, ok, paginated

router = APIRouter(prefix="/categories", tags=["Inventory - Medication Categories"])


def _to_response(entity) -> MedicationCategoryResponse:
    return MedicationCategoryResponse(
        id=entity.id,
        name=entity.name,
        description=entity.description,
        created_at=entity.created_at,
    )


@router.get("", summary="List medication categories")
async def list_categories(
    search: Optional[str] = Query(None, description="Search by name"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    repo: CategoryRepository = Depends(get_category_repo),
    _user_id: str = Depends(get_optional_user_id),
):
    items, total = await repo.find_all(search=search, page=page, page_size=page_size)
    data = [_to_response(c) for c in items]
    return paginated(data, total, page, page_size, "Categories retrieved")


@router.get("/{category_id}", summary="Get category by ID")
async def get_category(
    category_id: str,
    repo: CategoryRepository = Depends(get_category_repo),
    _user_id: str = Depends(get_optional_user_id),
):
    entity = await repo.find_by_id(category_id)
    if not entity:
        raise NotFoundException("Category not found")
    return ok(data=_to_response(entity), message="Category retrieved")


@router.post("", summary="Create medication category", status_code=201)
async def create_category(
    body: MedicationCategoryCreate,
    repo: CategoryRepository = Depends(get_category_repo),
    user_id: str = Depends(get_current_user_id),
):
    existing = await repo.find_by_name(body.name)
    if existing:
        raise ConflictException(f"Category '{body.name}' already exists")

    entity = await repo.create(
        data={"name": body.name, "description": body.description},
        created_by=user_id,
    )
    return created(data=_to_response(entity), message="Category created")


@router.patch("/{category_id}", summary="Update medication category")
async def update_category(
    category_id: str,
    body: MedicationCategoryUpdate,
    repo: CategoryRepository = Depends(get_category_repo),
    user_id: str = Depends(get_current_user_id),
):
    existing = await repo.find_by_id(category_id)
    if not existing:
        raise NotFoundException("Category not found")

    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise NotFoundException("No fields to update")

    entity = await repo.update(id=category_id, data=updates, updated_by=user_id)
    return ok(data=_to_response(entity), message="Category updated")


@router.delete("/{category_id}", summary="Delete category (soft-delete)")
async def delete_category(
    category_id: str,
    repo: CategoryRepository = Depends(get_category_repo),
    user_id: str = Depends(get_current_user_id),
):
    deleted = await repo.soft_delete(id=category_id, deleted_by=user_id)
    if not deleted:
        raise NotFoundException("Category not found")
    return ok(message="Category deleted")
