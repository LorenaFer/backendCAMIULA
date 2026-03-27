"""Implementación SQLAlchemy del repositorio de despachos."""

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlalchemy import func, select, update as sql_update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.inventory.domain.entities.dispatch import Dispatch, DispatchItem
from app.modules.inventory.domain.repositories.dispatch_repository import (
    DispatchRepository,
)
from app.modules.inventory.infrastructure.models import DispatchItemModel, DispatchModel
from app.shared.database.mixins import RecordStatus


class SQLAlchemyDispatchRepository(DispatchRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ──────────────────────────────────────────────────────────
    # Conversión
    # ──────────────────────────────────────────────────────────

    @staticmethod
    def _item_to_entity(m: DispatchItemModel) -> DispatchItem:
        return DispatchItem(
            id=m.id,
            fk_dispatch_id=m.fk_dispatch_id,
            fk_batch_id=m.fk_batch_id,
            fk_medication_id=m.fk_medication_id,
            quantity_dispatched=m.quantity_dispatched,
        )

    @staticmethod
    def _to_entity(
        model: DispatchModel, items: list[DispatchItemModel]
    ) -> Dispatch:
        return Dispatch(
            id=model.id,
            fk_prescription_id=model.fk_prescription_id,
            fk_patient_id=model.fk_patient_id,
            fk_pharmacist_id=model.fk_pharmacist_id,
            dispatch_date=model.dispatch_date.isoformat(),
            dispatch_status=model.dispatch_status,
            notes=model.notes,
            items=[SQLAlchemyDispatchRepository._item_to_entity(i) for i in items],
            created_at=model.created_at.isoformat() if model.created_at else None,
            created_by=model.created_by,
        )

    async def _load_items(self, dispatch_id: str) -> list[DispatchItemModel]:
        result = await self._session.execute(
            select(DispatchItemModel).where(
                DispatchItemModel.fk_dispatch_id == dispatch_id,
                DispatchItemModel.status == RecordStatus.ACTIVE,
            )
        )
        return result.scalars().all()

    # ──────────────────────────────────────────────────────────
    # Consultas
    # ──────────────────────────────────────────────────────────

    async def find_by_id(self, id: str) -> Optional[Dispatch]:
        result = await self._session.execute(
            select(DispatchModel).where(
                DispatchModel.id == id,
                DispatchModel.status == RecordStatus.ACTIVE,
            )
        )
        m = result.scalar_one_or_none()
        if not m:
            return None
        items = await self._load_items(id)
        return self._to_entity(m, items)

    async def find_by_prescription(self, fk_prescription_id: str) -> list[Dispatch]:
        result = await self._session.execute(
            select(DispatchModel).where(
                DispatchModel.fk_prescription_id == fk_prescription_id,
                DispatchModel.status == RecordStatus.ACTIVE,
            )
        )
        dispatches = []
        for m in result.scalars().all():
            items = await self._load_items(m.id)
            dispatches.append(self._to_entity(m, items))
        return dispatches

    async def find_by_patient(
        self,
        fk_patient_id: str,
        prescription_number: Optional[str],
        status: Optional[str],
        date_from: Optional[str],
        date_to: Optional[str],
        page: int,
        page_size: int,
    ) -> tuple[list[Dispatch], int]:
        q = select(DispatchModel).where(
            DispatchModel.fk_patient_id == fk_patient_id,
            DispatchModel.status == RecordStatus.ACTIVE,
        )
        if status:
            q = q.where(DispatchModel.dispatch_status == status)
        if date_from:
            q = q.where(DispatchModel.dispatch_date >= datetime.fromisoformat(date_from))
        if date_to:
            q = q.where(DispatchModel.dispatch_date <= datetime.fromisoformat(date_to))

        total = (
            await self._session.execute(select(func.count()).select_from(q.subquery()))
        ).scalar_one()
        offset = (page - 1) * page_size
        result = await self._session.execute(
            q.order_by(DispatchModel.dispatch_date.desc()).offset(offset).limit(page_size)
        )
        dispatches = []
        for m in result.scalars().all():
            items = await self._load_items(m.id)
            dispatches.append(self._to_entity(m, items))
        return dispatches, total

    async def get_monthly_consumption(
        self,
        fk_patient_id: str,
        fk_medication_id: str,
        month: str,
        year: int,
    ) -> int:
        """
        CTE optimizada: suma de quantity_dispatched para un paciente/medicamento
        en un mes específico. Incluye solo despachos con status != 'cancelled'.
        """
        from sqlalchemy import text

        result = await self._session.execute(
            text("""
                WITH dispatches_in_month AS (
                    SELECT d.id
                    FROM dispatches d
                    WHERE d.fk_patient_id = :patient_id
                      AND EXTRACT(MONTH FROM d.dispatch_date) = :month
                      AND EXTRACT(YEAR  FROM d.dispatch_date) = :year
                      AND d.dispatch_status != 'cancelled'
                      AND d.status = 'A'
                )
                SELECT COALESCE(SUM(di.quantity_dispatched), 0)
                FROM dispatch_items di
                WHERE di.fk_dispatch_id IN (SELECT id FROM dispatches_in_month)
                  AND di.fk_medication_id = :medication_id
                  AND di.status = 'A'
            """),
            {
                "patient_id": fk_patient_id,
                "month": int(month),
                "year": year,
                "medication_id": fk_medication_id,
            },
        )
        return result.scalar_one()

    # ──────────────────────────────────────────────────────────
    # Escritura
    # ──────────────────────────────────────────────────────────

    async def create(self, data: dict, created_by: str) -> Dispatch:
        """
        Crea el registro de despacho y sus ítems en un solo flush.
        Se asume que la sesión está dentro de una transacción abierta
        (gestionada por get_db() en la capa de presentación).
        """
        items_data: list[dict] = data.pop("items", [])
        dispatch_id = str(uuid4())

        model = DispatchModel(
            id=dispatch_id,
            created_by=created_by,
            **data,
        )
        self._session.add(model)
        await self._session.flush()

        item_models = []
        for item in items_data:
            im = DispatchItemModel(
                id=str(uuid4()),
                fk_dispatch_id=dispatch_id,
                created_by=created_by,
                **item,
            )
            self._session.add(im)
            item_models.append(im)

        await self._session.flush()
        return self._to_entity(model, item_models)

    async def update_status(self, id: str, new_status: str, updated_by: str) -> None:
        await self._session.execute(
            sql_update(DispatchModel)
            .where(DispatchModel.id == id)
            .values(
                dispatch_status=new_status,
                updated_at=datetime.now(timezone.utc),
                updated_by=updated_by,
            )
        )
