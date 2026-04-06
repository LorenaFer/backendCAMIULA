"""SQLAlchemy implementation of the Supplier repository."""

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlalchemy import func, select, update as sql_update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.inventory.domain.entities.supplier import Supplier
from app.modules.inventory.domain.repositories.supplier_repository import (
    SupplierRepository,
)
from app.modules.inventory.infrastructure.models import SupplierModel
from app.shared.database.mixins import RecordStatus


class SQLAlchemySupplierRepository(SupplierRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ------------------------------------------------------------------
    # Conversion
    # ------------------------------------------------------------------

    @staticmethod
    def _to_entity(model: SupplierModel) -> Supplier:
        return Supplier(
            id=model.id,
            name=model.name,
            rif=model.rif,
            phone=model.phone,
            email=model.email,
            contact_name=model.contact_name,
            payment_terms=model.payment_terms,
            supplier_status=model.supplier_status,
            created_at=model.created_at.isoformat() if model.created_at else None,
            created_by=model.created_by,
        )

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    async def find_all(
        self,
        search: Optional[str],
        status: Optional[str],
        page: int,
        page_size: int,
    ) -> tuple[list[Supplier], int]:
        q = select(SupplierModel).where(SupplierModel.status == RecordStatus.ACTIVE)

        if search:
            q = q.where(SupplierModel.name.ilike(f"%{search}%"))
        if status:
            q = q.where(SupplierModel.supplier_status == status)

        total = (
            await self._session.execute(select(func.count()).select_from(q.subquery()))
        ).scalar_one()

        offset = (page - 1) * page_size
        result = await self._session.execute(
            q.order_by(SupplierModel.name).offset(offset).limit(page_size)
        )
        return [self._to_entity(m) for m in result.scalars().all()], total

    async def find_by_id(self, id: str) -> Optional[Supplier]:
        result = await self._session.execute(
            select(SupplierModel).where(
                SupplierModel.id == id,
                SupplierModel.status == RecordStatus.ACTIVE,
            )
        )
        m = result.scalar_one_or_none()
        return self._to_entity(m) if m else None

    async def find_by_rif(self, rif: str) -> Optional[Supplier]:
        result = await self._session.execute(
            select(SupplierModel).where(
                SupplierModel.rif == rif,
                SupplierModel.status == RecordStatus.ACTIVE,
            )
        )
        m = result.scalar_one_or_none()
        return self._to_entity(m) if m else None

    async def find_options(self) -> list[Supplier]:
        result = await self._session.execute(
            select(SupplierModel)
            .where(
                SupplierModel.status == RecordStatus.ACTIVE,
                SupplierModel.supplier_status == "active",
            )
            .order_by(SupplierModel.name)
        )
        return [self._to_entity(m) for m in result.scalars().all()]

    # ------------------------------------------------------------------
    # Writes
    # ------------------------------------------------------------------

    async def create(self, data: dict, created_by: str) -> Supplier:
        model = SupplierModel(id=str(uuid4()), created_by=created_by, **data)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def update(self, id: str, data: dict, updated_by: str) -> Supplier:
        data["updated_by"] = updated_by
        data["updated_at"] = datetime.now(timezone.utc)
        await self._session.execute(
            sql_update(SupplierModel)
            .where(SupplierModel.id == id)
            .values(**data)
        )
        await self._session.flush()
        return await self.find_by_id(id)

    async def soft_delete(self, id: str, deleted_by: str) -> None:
        await self._session.execute(
            sql_update(SupplierModel)
            .where(SupplierModel.id == id)
            .values(
                status=RecordStatus.TRASH,
                deleted_at=datetime.now(timezone.utc),
                deleted_by=deleted_by,
            )
        )
