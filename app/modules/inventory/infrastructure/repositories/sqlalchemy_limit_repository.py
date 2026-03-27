"""Implementación SQLAlchemy del repositorio de límites y excepciones de despacho."""

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlalchemy import func, or_, select, update as sql_update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.inventory.domain.entities.dispatch_limit import (
    DispatchException,
    DispatchLimit,
)
from app.modules.inventory.domain.repositories.limit_repository import LimitRepository
from app.modules.inventory.infrastructure.models import (
    DispatchExceptionModel,
    DispatchLimitModel,
)
from app.shared.database.mixins import RecordStatus


class SQLAlchemyLimitRepository(LimitRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ──────────────────────────────────────────────────────────
    # Conversión
    # ──────────────────────────────────────────────────────────

    @staticmethod
    def _limit_to_entity(m: DispatchLimitModel) -> DispatchLimit:
        return DispatchLimit(
            id=m.id,
            fk_medication_id=m.fk_medication_id,
            monthly_max_quantity=m.monthly_max_quantity,
            applies_to=m.applies_to,
            active=m.active,
            created_at=m.created_at.isoformat() if m.created_at else None,
            created_by=m.created_by,
        )

    @staticmethod
    def _exception_to_entity(m: DispatchExceptionModel) -> DispatchException:
        return DispatchException(
            id=m.id,
            fk_patient_id=m.fk_patient_id,
            fk_medication_id=m.fk_medication_id,
            authorized_quantity=m.authorized_quantity,
            valid_from=m.valid_from.isoformat(),
            valid_until=m.valid_until.isoformat(),
            reason=m.reason,
            authorized_by=m.authorized_by,
            created_at=m.created_at.isoformat() if m.created_at else None,
            created_by=m.created_by,
        )

    # ──────────────────────────────────────────────────────────
    # Límites — consultas
    # ──────────────────────────────────────────────────────────

    async def find_all_limits(
        self,
        medication_id: Optional[str],
        page: int,
        page_size: int,
    ) -> tuple[list[DispatchLimit], int]:
        q = select(DispatchLimitModel).where(
            DispatchLimitModel.status == RecordStatus.ACTIVE
        )
        if medication_id:
            q = q.where(DispatchLimitModel.fk_medication_id == medication_id)

        total = (
            await self._session.execute(select(func.count()).select_from(q.subquery()))
        ).scalar_one()
        offset = (page - 1) * page_size
        result = await self._session.execute(q.offset(offset).limit(page_size))
        return [self._limit_to_entity(m) for m in result.scalars().all()], total

    async def find_limit_by_id(self, id: str) -> Optional[DispatchLimit]:
        result = await self._session.execute(
            select(DispatchLimitModel).where(
                DispatchLimitModel.id == id,
                DispatchLimitModel.status == RecordStatus.ACTIVE,
            )
        )
        m = result.scalar_one_or_none()
        return self._limit_to_entity(m) if m else None

    async def find_active_limit(
        self, fk_medication_id: str, applies_to: str
    ) -> Optional[DispatchLimit]:
        """
        Busca el límite activo más específico para el medicamento.
        Prioridad: límite por applies_to exacto → límite global ("all").
        """
        result = await self._session.execute(
            select(DispatchLimitModel)
            .where(
                DispatchLimitModel.fk_medication_id == fk_medication_id,
                DispatchLimitModel.active.is_(True),
                DispatchLimitModel.status == RecordStatus.ACTIVE,
                or_(
                    DispatchLimitModel.applies_to == applies_to,
                    DispatchLimitModel.applies_to == "all",
                ),
            )
            .order_by(
                # El límite específico (no "all") tiene prioridad
                (DispatchLimitModel.applies_to == applies_to).desc()
            )
            .limit(1)
        )
        m = result.scalar_one_or_none()
        return self._limit_to_entity(m) if m else None

    # ──────────────────────────────────────────────────────────
    # Límites — escritura
    # ──────────────────────────────────────────────────────────

    async def create_limit(self, data: dict, created_by: str) -> DispatchLimit:
        model = DispatchLimitModel(id=str(uuid4()), created_by=created_by, **data)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._limit_to_entity(model)

    async def update_limit(self, id: str, data: dict, updated_by: str) -> DispatchLimit:
        data["updated_at"] = datetime.now(timezone.utc)
        data["updated_by"] = updated_by
        await self._session.execute(
            sql_update(DispatchLimitModel)
            .where(DispatchLimitModel.id == id)
            .values(**data)
        )
        await self._session.flush()
        return await self.find_limit_by_id(id)

    # ──────────────────────────────────────────────────────────
    # Excepciones — consultas
    # ──────────────────────────────────────────────────────────

    async def find_all_exceptions(
        self,
        patient_id: Optional[str],
        medication_id: Optional[str],
        page: int,
        page_size: int,
    ) -> tuple[list[DispatchException], int]:
        q = select(DispatchExceptionModel).where(
            DispatchExceptionModel.status == RecordStatus.ACTIVE
        )
        if patient_id:
            q = q.where(DispatchExceptionModel.fk_patient_id == patient_id)
        if medication_id:
            q = q.where(DispatchExceptionModel.fk_medication_id == medication_id)

        total = (
            await self._session.execute(select(func.count()).select_from(q.subquery()))
        ).scalar_one()
        offset = (page - 1) * page_size
        result = await self._session.execute(q.offset(offset).limit(page_size))
        return [self._exception_to_entity(m) for m in result.scalars().all()], total

    async def find_active_exception(
        self,
        fk_patient_id: str,
        fk_medication_id: str,
        reference_date: str,
    ) -> Optional[DispatchException]:
        """Retorna la excepción vigente para (paciente, medicamento, fecha)."""
        from datetime import date as date_type

        ref = date_type.fromisoformat(reference_date)
        result = await self._session.execute(
            select(DispatchExceptionModel)
            .where(
                DispatchExceptionModel.fk_patient_id == fk_patient_id,
                DispatchExceptionModel.fk_medication_id == fk_medication_id,
                DispatchExceptionModel.valid_from <= ref,
                DispatchExceptionModel.valid_until >= ref,
                DispatchExceptionModel.status == RecordStatus.ACTIVE,
            )
            .limit(1)
        )
        m = result.scalar_one_or_none()
        return self._exception_to_entity(m) if m else None

    # ──────────────────────────────────────────────────────────
    # Excepciones — escritura
    # ──────────────────────────────────────────────────────────

    async def create_exception(self, data: dict, created_by: str) -> DispatchException:
        model = DispatchExceptionModel(id=str(uuid4()), created_by=created_by, **data)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._exception_to_entity(model)
