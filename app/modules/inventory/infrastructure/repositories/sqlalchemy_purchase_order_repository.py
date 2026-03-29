"""Implementación SQLAlchemy del repositorio de órdenes de compra."""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func, select, update as sql_update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.inventory.domain.entities.purchase_order import (
    PurchaseOrder,
    PurchaseOrderItem,
)
from app.modules.inventory.domain.repositories.purchase_order_repository import (
    PurchaseOrderRepository,
)
from app.modules.inventory.infrastructure.models import (
    PurchaseOrderItemModel,
    PurchaseOrderModel,
)
from app.shared.database.mixins import RecordStatus


class SQLAlchemyPurchaseOrderRepository(PurchaseOrderRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ──────────────────────────────────────────────────────────
    # Conversión ORM → entidad de dominio
    # ──────────────────────────────────────────────────────────

    @staticmethod
    def _item_to_entity(model: PurchaseOrderItemModel) -> PurchaseOrderItem:
        return PurchaseOrderItem(
            id=model.id,
            fk_purchase_order_id=model.fk_purchase_order_id,
            fk_medication_id=model.fk_medication_id,
            quantity_ordered=model.quantity_ordered,
            quantity_received=model.quantity_received,
            item_status=model.item_status,
            unit_cost=float(model.unit_cost) if model.unit_cost is not None else None,
        )

    @staticmethod
    def _to_entity(
        model: PurchaseOrderModel, items: list[PurchaseOrderItem]
    ) -> PurchaseOrder:
        return PurchaseOrder(
            id=model.id,
            fk_supplier_id=model.fk_supplier_id,
            order_number=model.order_number,
            order_date=model.order_date.isoformat(),
            order_status=model.order_status,
            items=items,
            expected_date=model.expected_date.isoformat() if model.expected_date else None,
            notes=model.notes,
            created_at=model.created_at.isoformat() if model.created_at else None,
            created_by=model.created_by,
        )

    # ──────────────────────────────────────────────────────────
    # Consultas
    # ──────────────────────────────────────────────────────────

    async def find_by_id(self, id: str) -> Optional[PurchaseOrder]:
        result = await self._session.execute(
            select(PurchaseOrderModel).where(
                PurchaseOrderModel.id == id,
                PurchaseOrderModel.status == RecordStatus.ACTIVE,
            )
        )
        order_model = result.scalar_one_or_none()
        if not order_model:
            return None

        items_result = await self._session.execute(
            select(PurchaseOrderItemModel).where(
                PurchaseOrderItemModel.fk_purchase_order_id == id,
                PurchaseOrderItemModel.status == RecordStatus.ACTIVE,
            )
        )
        items = [
            self._item_to_entity(m) for m in items_result.scalars().all()
        ]
        return self._to_entity(order_model, items)

    async def find_item_by_id(self, item_id: str) -> Optional[PurchaseOrderItem]:
        result = await self._session.execute(
            select(PurchaseOrderItemModel).where(
                PurchaseOrderItemModel.id == item_id,
                PurchaseOrderItemModel.status == RecordStatus.ACTIVE,
            )
        )
        model = result.scalar_one_or_none()
        return self._item_to_entity(model) if model else None

    async def all_items_received(self, order_id: str) -> bool:
        """Verifica si todos los ítems activos de la orden tienen
        quantity_received >= quantity_ordered.

        Un solo query con COUNT + FILTER — O(log n) con índice en fk_purchase_order_id.
        """
        result = await self._session.execute(
            select(
                func.count().label("total"),
                func.count().filter(
                    PurchaseOrderItemModel.quantity_received
                    >= PurchaseOrderItemModel.quantity_ordered
                ).label("completed"),
            )
            .where(
                PurchaseOrderItemModel.fk_purchase_order_id == order_id,
                PurchaseOrderItemModel.status == RecordStatus.ACTIVE,
            )
        )
        row = result.one()
        return row.total > 0 and row.total == row.completed

    # ──────────────────────────────────────────────────────────
    # Escritura
    # ──────────────────────────────────────────────────────────

    async def update_order_status(
        self, id: str, status: str, updated_by: str
    ) -> None:
        await self._session.execute(
            sql_update(PurchaseOrderModel)
            .where(PurchaseOrderModel.id == id)
            .values(
                order_status=status,
                updated_at=datetime.now(timezone.utc),
                updated_by=updated_by,
            )
        )
        await self._session.flush()

    async def increment_item_received(
        self,
        item_id: str,
        quantity_delta: int,
        item_status: str,
        unit_cost: Optional[float],
        updated_by: str,
    ) -> None:
        """Incrementa quantity_received con operación DB-side para evitar
        condiciones de carrera ante recepciones concurrentes."""
        values: dict = {
            "quantity_received": (
                PurchaseOrderItemModel.quantity_received + quantity_delta
            ),
            "item_status": item_status,
            "updated_at": datetime.now(timezone.utc),
            "updated_by": updated_by,
        }
        if unit_cost is not None:
            values["unit_cost"] = unit_cost

        await self._session.execute(
            sql_update(PurchaseOrderItemModel)
            .where(PurchaseOrderItemModel.id == item_id)
            .values(**values)
        )
        await self._session.flush()
