"""Implementación SQLAlchemy del repositorio de órdenes de compra."""

from datetime import date, datetime, timezone
from typing import List, Optional, Tuple
from uuid import uuid4

from sqlalchemy import func, select, update as sql_update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.inventory.domain.entities.purchase_order import (
    MedicationEmbed,
    PurchaseOrder,
    PurchaseOrderItem,
    SupplierEmbed,
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
        med_embed = None
        if hasattr(model, "medication") and model.medication:
            m = model.medication
            med_embed = MedicationEmbed(
                id=m.id,
                code=m.code,
                generic_name=m.generic_name,
                pharmaceutical_form=m.pharmaceutical_form,
                unit_measure=m.unit_measure,
            )
        return PurchaseOrderItem(
            id=model.id,
            fk_purchase_order_id=model.fk_purchase_order_id,
            fk_medication_id=model.fk_medication_id,
            quantity_ordered=model.quantity_ordered,
            quantity_received=model.quantity_received,
            item_status=model.item_status,
            unit_cost=float(model.unit_cost) if model.unit_cost is not None else None,
            medication=med_embed,
        )

    @staticmethod
    def _to_entity(
        model: PurchaseOrderModel, items: list[PurchaseOrderItem]
    ) -> PurchaseOrder:
        supplier_embed = None
        if hasattr(model, "supplier") and model.supplier:
            s = model.supplier
            supplier_embed = SupplierEmbed(
                id=s.id,
                name=s.name,
                rif=s.rif if hasattr(s, "rif") else None,
            )

        total_amount = sum(
            (it.unit_cost or 0) * it.quantity_ordered for it in items
        )

        return PurchaseOrder(
            id=model.id,
            fk_supplier_id=model.fk_supplier_id,
            order_number=model.order_number,
            order_date=model.order_date.isoformat() if model.order_date else None,
            order_status=model.order_status,
            items=items,
            expected_date=model.expected_date.isoformat() if model.expected_date else None,
            notes=model.notes,
            total_amount=total_amount,
            supplier=supplier_embed,
            sent_at=model.sent_at.isoformat() if hasattr(model, "sent_at") and model.sent_at else None,
            sent_by=model.sent_by if hasattr(model, "sent_by") else None,
            received_at=model.received_at.isoformat() if hasattr(model, "received_at") and model.received_at else None,
            received_by=model.received_by if hasattr(model, "received_by") else None,
            created_at=model.created_at.isoformat() if model.created_at else None,
            created_by=model.created_by,
        )

    # ──────────────────────────────────────────────────────────
    # Consultas
    # ──────────────────────────────────────────────────────────

    def _model_to_entity(self, order_model: PurchaseOrderModel) -> PurchaseOrder:
        """Convert ORM model (with eager-loaded relationships) to entity."""
        items = [
            self._item_to_entity(m)
            for m in (order_model.items_rel or [])
            if m.status == RecordStatus.ACTIVE or (hasattr(m.status, 'value') and m.status.value == 'A')
        ]
        return self._to_entity(order_model, items)

    async def find_by_id(self, id: str) -> Optional[PurchaseOrder]:
        result = await self._session.execute(
            select(PurchaseOrderModel).where(
                PurchaseOrderModel.id == id,
                PurchaseOrderModel.status == RecordStatus.ACTIVE,
            )
        )
        order_model = result.unique().scalar_one_or_none()
        if not order_model:
            return None
        return self._model_to_entity(order_model)

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

    async def find_all(
        self, page: int = 1, page_size: int = 20
    ) -> Tuple[List[PurchaseOrder], int]:
        base = select(PurchaseOrderModel).where(
            PurchaseOrderModel.status == RecordStatus.ACTIVE
        )
        count_q = select(func.count()).select_from(base.subquery())
        total = (await self._session.execute(count_q)).scalar_one()

        offset = (page - 1) * page_size
        result = await self._session.execute(
            base.order_by(PurchaseOrderModel.order_date.desc())
            .offset(offset)
            .limit(page_size)
        )
        orders = [
            self._model_to_entity(m) for m in result.unique().scalars().all()
        ]
        return orders, total

    async def get_next_order_number(self) -> str:
        year = date.today().year
        result = await self._session.execute(
            select(func.count()).select_from(
                select(PurchaseOrderModel.id)
                .where(PurchaseOrderModel.order_number.like(f"OC-{year}-%"))
                .subquery()
            )
        )
        count = result.scalar_one()
        return f"OC-{year}-{count + 1:04d}"

    async def create(self, data: dict, created_by: str) -> PurchaseOrder:
        items_data = data.pop("items", [])
        order_id = str(uuid4())

        if isinstance(data.get("expected_date"), str):
            data["expected_date"] = date.fromisoformat(data["expected_date"])
        if isinstance(data.get("order_date"), str):
            data["order_date"] = date.fromisoformat(data["order_date"])

        model = PurchaseOrderModel(id=order_id, created_by=created_by, **data)
        self._session.add(model)
        await self._session.flush()

        item_models = []
        for item in items_data:
            im = PurchaseOrderItemModel(
                id=str(uuid4()),
                fk_purchase_order_id=order_id,
                fk_medication_id=item["medication_id"],
                quantity_ordered=item["quantity_ordered"],
                quantity_received=0,
                unit_cost=item.get("unit_cost"),
                item_status="pending",
                created_by=created_by,
            )
            self._session.add(im)
            item_models.append(im)

        await self._session.flush()
        items = [self._item_to_entity(m) for m in item_models]
        return self._to_entity(model, items)

    # ──────────────────────────────────────────────────────────
    # Escritura
    # ──────────────────────────────────────────────────────────

    async def update_order_status(
        self, id: str, status: str, updated_by: str, **extra
    ) -> None:
        values = {
            "order_status": status,
            "updated_at": datetime.now(timezone.utc),
            "updated_by": updated_by,
            **extra,
        }
        await self._session.execute(
            sql_update(PurchaseOrderModel)
            .where(PurchaseOrderModel.id == id)
            .values(**values)
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
