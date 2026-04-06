"""SQLAlchemy implementation of the CategoryRepository."""

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlalchemy import func, select, update as sql_update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.inventory.domain.entities.category import MedicationCategory
from app.modules.inventory.domain.repositories.category_repository import (
    CategoryRepository,
)
from app.modules.inventory.infrastructure.models import MedicationCategoryModel
from app.shared.database.mixins import RecordStatus


class SQLAlchemyCategoryRepository(CategoryRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _to_entity(model: MedicationCategoryModel) -> MedicationCategory:
        return MedicationCategory(
            id=model.id,
            name=model.name,
            description=model.description,
            created_at=model.created_at.isoformat() if model.created_at else None,
            created_by=model.created_by,
        )

    async def find_all(
        self, search: Optional[str], page: int, page_size: int
    ) -> tuple[list[MedicationCategory], int]:
        q = select(MedicationCategoryModel).where(
            MedicationCategoryModel.status == RecordStatus.ACTIVE
        )
        if search:
            q = q.where(MedicationCategoryModel.name.ilike(f"%{search}%"))

        total = (
            await self._session.execute(select(func.count()).select_from(q.subquery()))
        ).scalar_one()

        offset = (page - 1) * page_size
        result = await self._session.execute(
            q.order_by(MedicationCategoryModel.name).offset(offset).limit(page_size)
        )
        return [self._to_entity(m) for m in result.scalars().all()], total

    async def find_by_id(self, id: str) -> Optional[MedicationCategory]:
        result = await self._session.execute(
            select(MedicationCategoryModel).where(
                MedicationCategoryModel.id == id,
                MedicationCategoryModel.status == RecordStatus.ACTIVE,
            )
        )
        m = result.scalar_one_or_none()
        return self._to_entity(m) if m else None

    async def find_by_name(self, name: str) -> Optional[MedicationCategory]:
        result = await self._session.execute(
            select(MedicationCategoryModel).where(
                MedicationCategoryModel.name == name,
                MedicationCategoryModel.status == RecordStatus.ACTIVE,
            )
        )
        m = result.scalar_one_or_none()
        return self._to_entity(m) if m else None

    async def create(self, data: dict, created_by: str) -> MedicationCategory:
        model = MedicationCategoryModel(
            id=str(uuid4()),
            created_by=created_by,
            **data,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def update(
        self, id: str, data: dict, updated_by: str
    ) -> Optional[MedicationCategory]:
        data["updated_at"] = datetime.now(timezone.utc)
        data["updated_by"] = updated_by
        await self._session.execute(
            sql_update(MedicationCategoryModel)
            .where(MedicationCategoryModel.id == id)
            .values(**data)
        )
        await self._session.flush()
        return await self.find_by_id(id)

    async def soft_delete(self, id: str, deleted_by: str) -> bool:
        result = await self._session.execute(
            sql_update(MedicationCategoryModel)
            .where(
                MedicationCategoryModel.id == id,
                MedicationCategoryModel.status == RecordStatus.ACTIVE,
            )
            .values(
                status=RecordStatus.TRASH,
                deleted_at=datetime.now(timezone.utc),
                deleted_by=deleted_by,
            )
        )
        return result.rowcount > 0
