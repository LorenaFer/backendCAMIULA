"""Implementación SQLAlchemy del repositorio de lotes (Batch)."""

from datetime import date, datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlalchemy import func, select, update as sql_update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.inventory.domain.entities.batch import Batch
from app.modules.inventory.domain.repositories.batch_repository import BatchRepository
from app.modules.inventory.infrastructure.models import BatchModel
from app.shared.database.mixins import RecordStatus


class SQLAlchemyBatchRepository(BatchRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ──────────────────────────────────────────────────────────
    # Conversión
    # ──────────────────────────────────────────────────────────

    @staticmethod
    def _to_entity(model: BatchModel) -> Batch:
        return Batch(
            id=model.id,
            fk_medication_id=model.fk_medication_id,
            fk_supplier_id=model.fk_supplier_id,
            fk_purchase_order_id=model.fk_purchase_order_id,
            lot_number=model.lot_number,
            expiration_date=model.expiration_date.isoformat(),
            quantity_received=model.quantity_received,
            quantity_available=model.quantity_available,
            unit_cost=float(model.unit_cost) if model.unit_cost is not None else None,
            received_at=model.received_at.isoformat(),
            batch_status=model.batch_status,
            created_at=model.created_at.isoformat() if model.created_at else None,
            created_by=model.created_by,
        )

    # ──────────────────────────────────────────────────────────
    # Consultas
    # ──────────────────────────────────────────────────────────

    async def find_all(
        self,
        medication_id: Optional[str],
        status: Optional[str],
        expiring_before: Optional[str],
        page: int,
        page_size: int,
    ) -> tuple[list[Batch], int]:
        q = select(BatchModel).where(BatchModel.status == RecordStatus.ACTIVE)

        if medication_id:
            q = q.where(BatchModel.fk_medication_id == medication_id)
        if status:
            q = q.where(BatchModel.batch_status == status)
        if expiring_before:
            q = q.where(BatchModel.expiration_date <= date.fromisoformat(expiring_before))

        total = (
            await self._session.execute(select(func.count()).select_from(q.subquery()))
        ).scalar_one()

        offset = (page - 1) * page_size
        result = await self._session.execute(
            q.order_by(BatchModel.expiration_date.asc()).offset(offset).limit(page_size)
        )
        return [self._to_entity(m) for m in result.scalars().all()], total

    async def find_by_id(self, id: str) -> Optional[Batch]:
        result = await self._session.execute(
            select(BatchModel).where(
                BatchModel.id == id,
                BatchModel.status == RecordStatus.ACTIVE,
            )
        )
        m = result.scalar_one_or_none()
        return self._to_entity(m) if m else None

    async def find_available_fefo(self, medication_id: str) -> list[Batch]:
        """
        Lotes availables ordenados FEFO (First Expired, First Out).

        Usa SELECT FOR UPDATE para serializar el acceso concurrente y
        garantizar que dos despachos simultáneos no lean el mismo stock
        sin haber actualizado la fila entre sí.
        """
        result = await self._session.execute(
            select(BatchModel)
            .where(
                BatchModel.fk_medication_id == medication_id,
                BatchModel.batch_status == "available",
                BatchModel.quantity_available > 0,
                BatchModel.status == RecordStatus.ACTIVE,
            )
            .order_by(
                BatchModel.expiration_date.asc(),
                BatchModel.created_at.asc(),
            )
            .with_for_update()
        )
        return [self._to_entity(m) for m in result.scalars().all()]

    # ──────────────────────────────────────────────────────────
    # Escritura
    # ──────────────────────────────────────────────────────────

    async def create(self, data: dict, created_by: str) -> Batch:
        model = BatchModel(id=str(uuid4()), created_by=created_by, **data)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def update_quantity(self, id: str, new_quantity: int, updated_by: str) -> None:
        new_status = "depleted" if new_quantity == 0 else "available"
        await self._session.execute(
            sql_update(BatchModel)
            .where(BatchModel.id == id)
            .values(
                quantity_available=new_quantity,
                batch_status=new_status,
                updated_at=datetime.now(timezone.utc),
                updated_by=updated_by,
            )
        )

    async def update_status(self, id: str, new_status: str, updated_by: str) -> None:
        await self._session.execute(
            sql_update(BatchModel)
            .where(BatchModel.id == id)
            .values(
                batch_status=new_status,
                updated_at=datetime.now(timezone.utc),
                updated_by=updated_by,
            )
        )
