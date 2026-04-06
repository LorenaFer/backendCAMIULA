"""Implementación SQLAlchemy del repositorio de medicamentos."""

from datetime import date, datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlalchemy import func, select, update as sql_update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.inventory.domain.entities.medication import Medication
from app.modules.inventory.domain.repositories.medication_repository import (
    MedicationRepository,
)
from app.modules.inventory.infrastructure.models import BatchModel, MedicationModel
from app.shared.database.mixins import RecordStatus


def _stock_subquery():
    """Subquery reutilizable: stock disponible por medicamento (lotes vigentes)."""
    today = date.today()
    return (
        select(
            BatchModel.fk_medication_id.label("med_id"),
            func.coalesce(func.sum(BatchModel.quantity_available), 0).label(
                "current_stock"
            ),
        )
        .where(
            BatchModel.status == RecordStatus.ACTIVE,
            BatchModel.batch_status == "available",
            BatchModel.expiration_date >= today,
            BatchModel.quantity_available > 0,
        )
        .group_by(BatchModel.fk_medication_id)
        .subquery()
    )


class SQLAlchemyMedicationRepository(MedicationRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ──────────────────────────────────────────────────────────
    # Conversión ORM → entidad de dominio
    # ──────────────────────────────────────────────────────────

    @staticmethod
    def _to_entity(model: MedicationModel, current_stock: int = 0) -> Medication:
        cat_name = None
        if hasattr(model, "category") and model.category is not None:
            cat_name = model.category.name
        return Medication(
            id=model.id,
            code=model.code,
            generic_name=model.generic_name,
            commercial_name=model.commercial_name,
            pharmaceutical_form=model.pharmaceutical_form,
            concentration=model.concentration,
            unit_measure=model.unit_measure,
            therapeutic_class=model.therapeutic_class,
            fk_category_id=model.fk_category_id,
            category_name=cat_name,
            controlled_substance=model.controlled_substance,
            requires_refrigeration=model.requires_refrigeration,
            medication_status=model.medication_status,
            current_stock=current_stock,
            created_at=model.created_at.isoformat() if model.created_at else None,
            created_by=model.created_by,
        )

    # ──────────────────────────────────────────────────────────
    # Consultas
    # ──────────────────────────────────────────────────────────

    async def find_all(
        self,
        search: Optional[str],
        status: Optional[str],
        therapeutic_class: Optional[str],
        page: int,
        page_size: int,
        category_id: Optional[str] = None,
    ) -> tuple[list[Medication], int]:
        stock_sq = _stock_subquery()

        base = (
            select(
                MedicationModel,
                func.coalesce(stock_sq.c.current_stock, 0).label("current_stock"),
            )
            .outerjoin(stock_sq, stock_sq.c.med_id == MedicationModel.id)
            .where(MedicationModel.status == RecordStatus.ACTIVE)
        )

        if search:
            base = base.where(
                MedicationModel.generic_name.ilike(f"%{search}%")
            )
        if status:
            base = base.where(MedicationModel.medication_status == status)
        if therapeutic_class:
            base = base.where(MedicationModel.therapeutic_class == therapeutic_class)
        if category_id:
            base = base.where(MedicationModel.fk_category_id == category_id)

        count_q = select(func.count()).select_from(base.subquery())
        total = (await self._session.execute(count_q)).scalar_one()

        offset = (page - 1) * page_size
        result = await self._session.execute(
            base.order_by(MedicationModel.generic_name).offset(offset).limit(page_size)
        )
        return [
            self._to_entity(row.MedicationModel, int(row.current_stock))
            for row in result.all()
        ], total

    async def find_by_id(self, id: str) -> Optional[Medication]:
        stock_sq = _stock_subquery()
        result = await self._session.execute(
            select(
                MedicationModel,
                func.coalesce(stock_sq.c.current_stock, 0).label("current_stock"),
            )
            .outerjoin(stock_sq, stock_sq.c.med_id == MedicationModel.id)
            .where(
                MedicationModel.id == id,
                MedicationModel.status == RecordStatus.ACTIVE,
            )
        )
        row = result.one_or_none()
        if not row:
            return None
        return self._to_entity(row.MedicationModel, int(row.current_stock))

    async def find_by_code(self, code: str) -> Optional[Medication]:
        result = await self._session.execute(
            select(MedicationModel).where(
                MedicationModel.code == code,
                MedicationModel.status == RecordStatus.ACTIVE,
            )
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def find_options(
        self, search: Optional[str] = None, limit: int = 100
    ) -> list[Medication]:
        """Lista simplificada para selects — stock calculado en un solo JOIN."""
        stock_sq = _stock_subquery()
        q = (
            select(
                MedicationModel,
                func.coalesce(stock_sq.c.current_stock, 0).label("current_stock"),
            )
            .outerjoin(stock_sq, stock_sq.c.med_id == MedicationModel.id)
            .where(
                MedicationModel.status == RecordStatus.ACTIVE,
                MedicationModel.medication_status == "active",
            )
        )
        if search:
            q = q.where(MedicationModel.generic_name.ilike(f"%{search}%"))
        q = q.order_by(MedicationModel.generic_name).limit(limit)
        result = await self._session.execute(q)
        return [
            self._to_entity(row.MedicationModel, int(row.current_stock))
            for row in result.all()
        ]

    async def get_current_stock(self, medication_id: str) -> int:
        result = await self._session.execute(
            select(func.coalesce(func.sum(BatchModel.quantity_available), 0)).where(
                BatchModel.fk_medication_id == medication_id,
                BatchModel.batch_status == "available",
                BatchModel.status == RecordStatus.ACTIVE,
            )
        )
        return result.scalar_one()

    # ──────────────────────────────────────────────────────────
    # Escritura
    # ──────────────────────────────────────────────────────────

    async def create(self, data: dict, created_by: str) -> Medication:
        med_id = str(uuid4())
        model = MedicationModel(
            id=med_id,
            created_by=created_by,
            **data,
        )
        self._session.add(model)
        await self._session.flush()
        # Re-fetch with joined category relationship
        return await self.find_by_id(med_id)

    async def update(self, id: str, data: dict, updated_by: str) -> Medication:
        data["updated_by"] = updated_by
        data["updated_at"] = datetime.now(timezone.utc)
        await self._session.execute(
            sql_update(MedicationModel)
            .where(MedicationModel.id == id)
            .values(**data)
        )
        await self._session.flush()
        return await self.find_by_id(id)

    async def soft_delete(self, id: str, deleted_by: str) -> None:
        await self._session.execute(
            sql_update(MedicationModel)
            .where(MedicationModel.id == id)
            .values(
                status=RecordStatus.TRASH,
                deleted_at=datetime.now(timezone.utc),
                deleted_by=deleted_by,
            )
        )
