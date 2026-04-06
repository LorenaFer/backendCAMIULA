"""Repositorio de reportes de inventario — consultas de solo lectura.

Todas las queries son agregaciones optimizadas con func.sum / func.count.
No se retornan entidades de dominio; se retornan DTOs directamente.
"""

from datetime import date, datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import and_, case, func, literal, or_, select, text, union_all
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.inventory.application.dtos.report_dto import (
    STOCK_THRESHOLD_CRITICAL,
    STOCK_THRESHOLD_LOW,
    ConsumptionItemDTO,
    ConsumptionReportDTO,
    EnrichedBatchDTO,
    ExpirationReportDTO,
    InventorySummaryDTO,
    LowStockReportDTO,
    MedicationOptionDTO,
    MovementItemDTO,
    MovementsReportDTO,
    StockItemDTO,
    StockReportDTO,
)
from app.modules.inventory.infrastructure.models import (
    BatchModel,
    DispatchItemModel,
    DispatchModel,
    MedicationModel,
    PrescriptionModel,
    PurchaseOrderModel,
)
from app.shared.database.mixins import RecordStatus


# SQL CASE WHEN expression that mirrors compute_stock_alert() from the DTOs.
# Kept as a module-level helper so both get_stock_report and get_inventory_summary
# can reuse it without duplicating the expression tree.
def _stock_alert_case(total_available_col, expired_batch_count_col=None):
    """Return a SQLAlchemy CASE expression for the stock alert level.

    Logic:
    - has expired batches AND zero usable stock → 'expired'
    - zero stock but no expired batches → 'critical' (out of stock, not expired)
    - stock <= 10 → 'critical'
    - stock <= 50 → 'low'
    - else → 'ok'
    """
    if expired_batch_count_col is not None:
        return case(
            (and_(total_available_col == 0, expired_batch_count_col > 0), literal("expired")),
            (total_available_col <= STOCK_THRESHOLD_CRITICAL, literal("critical")),
            (total_available_col <= STOCK_THRESHOLD_LOW, literal("low")),
            else_=literal("ok"),
        )
    return case(
        (total_available_col == 0, literal("expired")),
        (total_available_col <= STOCK_THRESHOLD_CRITICAL, literal("critical")),
        (total_available_col <= STOCK_THRESHOLD_LOW, literal("low")),
        else_=literal("ok"),
    )


class SQLAlchemyReportRepository:

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ──────────────────────────────────────────────────────────
    # Stock consolidado
    # ──────────────────────────────────────────────────────────

    async def _auto_expire_batches(self):
        """Mark batches as 'expired' if expiration_date < today.

        O(log n) — uses index on expiration_date. Runs once per report request.
        """
        today = date.today()
        await self._session.execute(
            text(
                "UPDATE batches SET batch_status = 'expired' "
                "WHERE batch_status = 'available' "
                "AND expiration_date < :today "
                "AND status = 'A'"
            ),
            {"today": today},
        )

    async def get_stock_report(self) -> StockReportDTO:
        """
        Calcula stock vigente por medicamento en un solo query con GROUP BY.
        Solo cuenta lotes cuya expiration_date >= hoy y batch_status = 'available'.

        stock_alert, critical_count y expired_count se computan directamente
        en SQL mediante CASE WHEN — sin post-procesamiento en Python.
        """
        # Auto-expire stale batches first
        await self._auto_expire_batches()

        today = date.today()

        # Subquery: usable (non-expired) batches
        usable_batches_sq = (
            select(
                BatchModel.fk_medication_id,
                func.coalesce(func.sum(BatchModel.quantity_available), 0).label(
                    "total_available"
                ),
                func.count(BatchModel.id).label("batch_count"),
                func.min(BatchModel.expiration_date).label("nearest_expiration"),
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

        # Subquery: count of expired batches per medication
        expired_batches_sq = (
            select(
                BatchModel.fk_medication_id,
                func.count(BatchModel.id).label("expired_count"),
            )
            .where(
                BatchModel.status == RecordStatus.ACTIVE,
                BatchModel.batch_status == "expired",
            )
            .group_by(BatchModel.fk_medication_id)
            .subquery()
        )

        total_available_col = func.coalesce(
            usable_batches_sq.c.total_available, 0
        )
        expired_count_col = func.coalesce(
            expired_batches_sq.c.expired_count, 0
        )
        stock_alert_expr = _stock_alert_case(
            total_available_col, expired_count_col
        ).label("stock_alert")

        rows = (
            await self._session.execute(
                select(
                    MedicationModel.id,
                    MedicationModel.code,
                    MedicationModel.generic_name,
                    MedicationModel.pharmaceutical_form,
                    MedicationModel.unit_measure,
                    total_available_col.label("total_available"),
                    func.coalesce(usable_batches_sq.c.batch_count, 0).label(
                        "batch_count"
                    ),
                    usable_batches_sq.c.nearest_expiration,
                    stock_alert_expr,
                )
                .outerjoin(
                    usable_batches_sq,
                    usable_batches_sq.c.fk_medication_id == MedicationModel.id,
                )
                .outerjoin(
                    expired_batches_sq,
                    expired_batches_sq.c.fk_medication_id == MedicationModel.id,
                )
                .where(
                    MedicationModel.status == RecordStatus.ACTIVE,
                    MedicationModel.medication_status == "active",
                )
                .order_by(total_available_col.asc())
            )
        ).all()

        critical_count = 0
        expired_count = 0
        items: list[StockItemDTO] = []
        for row in rows:
            alert = row.stock_alert
            if alert == "critical":
                critical_count += 1
            elif alert == "expired":
                expired_count += 1

            days: Optional[int] = None
            nearest_exp: Optional[str] = None
            if row.nearest_expiration:
                nearest_exp = row.nearest_expiration.isoformat()
                days = (row.nearest_expiration - today).days

            items.append(
                StockItemDTO(
                    medication_id=row.id,
                    code=row.code,
                    generic_name=row.generic_name,
                    pharmaceutical_form=row.pharmaceutical_form,
                    unit_measure=row.unit_measure,
                    total_available=int(row.total_available),
                    batch_count=int(row.batch_count),
                    nearest_expiration=nearest_exp,
                    days_to_expiration=days,
                    stock_alert=alert,
                )
            )

        generated_at = datetime.now(timezone.utc).isoformat()

        return StockReportDTO(
            generated_at=generated_at,
            items=items,
            total_medications=len(items),
            critical_count=critical_count,
            expired_count=expired_count,
        )

    # ──────────────────────────────────────────────────────────
    # Stock bajo / crítico (filtrado en SQL)
    # ──────────────────────────────────────────────────────────

    async def get_low_stock_report(self) -> LowStockReportDTO:
        """
        Retorna solo medicamentos con stock_alert in ('low', 'critical', 'expired').
        Filtra directamente en SQL con HAVING — sin materializar el reporte completo.
        Ordenado por criticidad: expired → critical → low.
        """
        today = date.today()

        usable_batches_sq = (
            select(
                BatchModel.fk_medication_id,
                func.coalesce(func.sum(BatchModel.quantity_available), 0).label(
                    "total_available"
                ),
                func.count(BatchModel.id).label("batch_count"),
                func.min(BatchModel.expiration_date).label("nearest_expiration"),
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

        total_available_col = func.coalesce(
            usable_batches_sq.c.total_available, 0
        )
        stock_alert_expr = _stock_alert_case(total_available_col)

        # Filtrar: solo stock <= STOCK_THRESHOLD_LOW (incluye critical y expired)
        rows = (
            await self._session.execute(
                select(
                    MedicationModel.id,
                    MedicationModel.code,
                    MedicationModel.generic_name,
                    MedicationModel.pharmaceutical_form,
                    MedicationModel.unit_measure,
                    total_available_col.label("total_available"),
                    func.coalesce(usable_batches_sq.c.batch_count, 0).label(
                        "batch_count"
                    ),
                    usable_batches_sq.c.nearest_expiration,
                    stock_alert_expr.label("stock_alert"),
                )
                .outerjoin(
                    usable_batches_sq,
                    usable_batches_sq.c.fk_medication_id == MedicationModel.id,
                )
                .where(
                    MedicationModel.status == RecordStatus.ACTIVE,
                    MedicationModel.medication_status == "active",
                    total_available_col <= STOCK_THRESHOLD_LOW,
                )
                .order_by(total_available_col.asc())
            )
        ).all()

        items: list[StockItemDTO] = []
        for row in rows:
            days: Optional[int] = None
            nearest_exp: Optional[str] = None
            if row.nearest_expiration:
                nearest_exp = row.nearest_expiration.isoformat()
                days = (row.nearest_expiration - today).days

            items.append(
                StockItemDTO(
                    medication_id=row.id,
                    code=row.code,
                    generic_name=row.generic_name,
                    pharmaceutical_form=row.pharmaceutical_form,
                    unit_measure=row.unit_measure,
                    total_available=int(row.total_available),
                    batch_count=int(row.batch_count),
                    nearest_expiration=nearest_exp,
                    days_to_expiration=days,
                    stock_alert=row.stock_alert,
                )
            )

        return LowStockReportDTO(
            generated_at=datetime.now(timezone.utc).isoformat(),
            items=items,
        )

    # ──────────────────────────────────────────────────────────
    # Resumen ejecutivo
    # ──────────────────────────────────────────────────────────

    async def get_inventory_summary(self) -> InventorySummaryDTO:
        """
        KPIs del dashboard: counts por nivel de alerta.

        Usa un solo query SQL con CASE WHEN + COUNT/SUM para calcular todos
        los KPIs directamente en la base de datos, sin materializar la lista
        completa de items que requiere get_stock_report().
        """
        today = date.today()

        usable_batches_sq = (
            select(
                BatchModel.fk_medication_id,
                func.coalesce(func.sum(BatchModel.quantity_available), 0).label(
                    "total_available"
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

        total_available_col = func.coalesce(
            usable_batches_sq.c.total_available, 0
        )
        stock_alert_expr = _stock_alert_case(total_available_col)

        row = (
            await self._session.execute(
                select(
                    func.count().label("total_active_skus"),
                    func.count().filter(
                        stock_alert_expr == "critical"
                    ).label("critical_count"),
                    func.count().filter(
                        stock_alert_expr == "low"
                    ).label("low_count"),
                    func.count().filter(
                        stock_alert_expr == "expired"
                    ).label("expired_count"),
                    func.coalesce(func.sum(total_available_col), 0).label(
                        "total_available_units"
                    ),
                )
                .select_from(MedicationModel)
                .outerjoin(
                    usable_batches_sq,
                    usable_batches_sq.c.fk_medication_id == MedicationModel.id,
                )
                .where(
                    MedicationModel.status == RecordStatus.ACTIVE,
                    MedicationModel.medication_status == "active",
                )
            )
        ).one()

        return InventorySummaryDTO(
            generated_at=datetime.now(timezone.utc).isoformat(),
            total_active_skus=int(row.total_active_skus),
            critical_count=int(row.critical_count),
            low_count=int(row.low_count),
            expired_count=int(row.expired_count),
            total_available_units=int(row.total_available_units),
        )

    # ──────────────────────────────────────────────────────────
    # Próximos a vencer
    # ──────────────────────────────────────────────────────────

    async def get_expiration_report(self, threshold_days: int) -> ExpirationReportDTO:
        """
        Retorna lotes availables cuya expiration_date <= hoy + threshold_days.
        Enriquece cada lote con datos del medicamento (campo `medication`).
        """
        today = date.today()
        cutoff = today + timedelta(days=threshold_days)

        # Subquery para stock actual del medicamento (solo lotes vigentes)
        stock_sq = (
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

        rows = (
            await self._session.execute(
                select(
                    BatchModel.id,
                    BatchModel.fk_medication_id,
                    BatchModel.fk_supplier_id,
                    BatchModel.lot_number,
                    BatchModel.expiration_date,
                    BatchModel.quantity_received,
                    BatchModel.quantity_available,
                    BatchModel.unit_cost,
                    BatchModel.batch_status,
                    BatchModel.received_at,
                    MedicationModel.code.label("med_code"),
                    MedicationModel.generic_name,
                    MedicationModel.pharmaceutical_form,
                    MedicationModel.unit_measure,
                    func.coalesce(stock_sq.c.current_stock, 0).label("current_stock"),
                )
                .join(MedicationModel, MedicationModel.id == BatchModel.fk_medication_id)
                .outerjoin(stock_sq, stock_sq.c.med_id == BatchModel.fk_medication_id)
                .where(
                    BatchModel.status == RecordStatus.ACTIVE,
                    BatchModel.batch_status == "available",
                    BatchModel.expiration_date >= today,
                    BatchModel.expiration_date <= cutoff,
                    MedicationModel.status == RecordStatus.ACTIVE,
                )
                .order_by(BatchModel.expiration_date.asc())
            )
        ).all()

        batches: list[EnrichedBatchDTO] = []
        for row in rows:
            med_opt = MedicationOptionDTO(
                id=row.fk_medication_id,
                code=row.med_code,
                generic_name=row.generic_name,
                pharmaceutical_form=row.pharmaceutical_form,
                unit_measure=row.unit_measure,
                current_stock=int(row.current_stock),
            )
            batches.append(
                EnrichedBatchDTO(
                    id=row.id,
                    fk_medication_id=row.fk_medication_id,
                    medication=med_opt,
                    fk_supplier_id=row.fk_supplier_id,
                    supplier_name=None,  # supplier join omitido por ahora
                    lot_number=row.lot_number,
                    expiration_date=row.expiration_date.isoformat(),
                    quantity_received=row.quantity_received,
                    quantity_available=row.quantity_available,
                    unit_cost=float(row.unit_cost) if row.unit_cost else None,
                    batch_status=row.batch_status,
                    received_at=row.received_at.isoformat(),
                )
            )

        return ExpirationReportDTO(
            generated_at=datetime.now(timezone.utc).isoformat(),
            threshold_days=threshold_days,
            batches=batches,
        )

    # ──────────────────────────────────────────────────────────
    # Consumo mensual
    # ──────────────────────────────────────────────────────────

    async def get_consumption_report(self, period: str) -> ConsumptionReportDTO:
        """
        Agrega despachos del mes indicado (formato YYYY-MM).

        Por cada medicamento devuelve:
            - total_dispatched: suma de quantity_dispatched
            - dispatch_count: número de despachos distintos
            - patient_count: número de pacientes distintos
        """
        year_str, month_str = period.split("-")
        year = int(year_str)
        month = int(month_str)

        rows = (
            await self._session.execute(
                select(
                    DispatchItemModel.fk_medication_id,
                    MedicationModel.generic_name,
                    func.sum(DispatchItemModel.quantity_dispatched).label(
                        "total_dispatched"
                    ),
                    func.count(
                        func.distinct(DispatchItemModel.fk_dispatch_id)
                    ).label("dispatch_count"),
                    func.count(func.distinct(DispatchModel.fk_patient_id)).label(
                        "patient_count"
                    ),
                )
                .join(
                    DispatchModel,
                    DispatchModel.id == DispatchItemModel.fk_dispatch_id,
                )
                .join(
                    MedicationModel,
                    MedicationModel.id == DispatchItemModel.fk_medication_id,
                )
                .where(
                    DispatchItemModel.status == RecordStatus.ACTIVE,
                    DispatchModel.status == RecordStatus.ACTIVE,
                    DispatchModel.dispatch_status != "cancelled",
                    func.extract("year", DispatchModel.dispatch_date) == year,
                    func.extract("month", DispatchModel.dispatch_date) == month,
                    MedicationModel.status == RecordStatus.ACTIVE,
                )
                .group_by(
                    DispatchItemModel.fk_medication_id,
                    MedicationModel.generic_name,
                )
                .order_by(
                    func.sum(DispatchItemModel.quantity_dispatched).desc()
                )
            )
        ).all()

        items = [
            ConsumptionItemDTO(
                medication_id=row.fk_medication_id,
                generic_name=row.generic_name,
                total_dispatched=int(row.total_dispatched),
                dispatch_count=int(row.dispatch_count),
                patient_count=int(row.patient_count),
            )
            for row in rows
        ]

        return ConsumptionReportDTO(period=period, items=items)

    # ──────────────────────────────────────────────────────────
    # Kardex / Movimientos
    # ──────────────────────────────────────────────────────────

    async def get_movements(
        self,
        medication_id: str,
        date_from: Optional[str],
        date_to: Optional[str],
        page: int,
        page_size: int,
    ) -> MovementsReportDTO:
        """
        Combina entradas (lotes recibidos) y salidas (despachos) de un medicamento
        en orden cronológico inverso (más reciente primero).

        Entradas: tabla batches — evento de ingreso al inventario.
        Salidas:  dispatch_items + dispatches — evento de despacho.
        """
        # Nombre del medicamento
        med_row = (
            await self._session.execute(
                select(MedicationModel.generic_name).where(
                    MedicationModel.id == medication_id,
                    MedicationModel.status == RecordStatus.ACTIVE,
                )
            )
        ).one_or_none()

        generic_name = med_row[0] if med_row else medication_id

        # ── Entries ───────────────────────────────────────────
        entries_q = (
            select(
                BatchModel.received_at.label("movement_date"),
                literal("entry").label("movement_type"),
                func.coalesce(
                    PurchaseOrderModel.order_number, BatchModel.lot_number
                ).label("reference"),
                BatchModel.lot_number,
                BatchModel.quantity_received.label("quantity"),
                BatchModel.unit_cost,
                literal(None).label("notes"),
            )
            .outerjoin(
                PurchaseOrderModel,
                PurchaseOrderModel.id == BatchModel.fk_purchase_order_id,
            )
            .where(
                BatchModel.fk_medication_id == medication_id,
                BatchModel.status == RecordStatus.ACTIVE,
            )
        )

        # ── Exits ────────────────────────────────────────────
        exits_q = (
            select(
                DispatchModel.dispatch_date.label("movement_date"),
                literal("exit").label("movement_type"),
                func.coalesce(
                    PrescriptionModel.prescription_number, DispatchModel.id
                ).label("reference"),
                literal(None).label("lot_number"),
                DispatchItemModel.quantity_dispatched.label("quantity"),
                literal(None).label("unit_cost"),
                DispatchModel.notes.label("notes"),
            )
            .join(
                DispatchModel,
                DispatchModel.id == DispatchItemModel.fk_dispatch_id,
            )
            .outerjoin(
                PrescriptionModel,
                PrescriptionModel.id == DispatchModel.fk_prescription_id,
            )
            .where(
                DispatchItemModel.fk_medication_id == medication_id,
                DispatchItemModel.status == RecordStatus.ACTIVE,
                DispatchModel.status == RecordStatus.ACTIVE,
                DispatchModel.dispatch_status != "cancelled",
            )
        )

        # Apply date filters
        if date_from:
            df = date.fromisoformat(date_from)
            entries_q = entries_q.where(BatchModel.received_at >= df)
            exits_q = exits_q.where(DispatchModel.dispatch_date >= df)
        if date_to:
            dt = date.fromisoformat(date_to)
            entries_q = entries_q.where(BatchModel.received_at <= dt)
            exits_q = exits_q.where(DispatchModel.dispatch_date <= dt)

        combined = union_all(entries_q, exits_q).subquery()

        # Total count
        total = (
            await self._session.execute(
                select(func.count()).select_from(combined)
            )
        ).scalar_one()

        # Paginated result
        offset = (page - 1) * page_size
        rows = (
            await self._session.execute(
                select(combined)
                .order_by(combined.c.movement_date.desc())
                .offset(offset)
                .limit(page_size)
            )
        ).all()

        items = [
            MovementItemDTO(
                movement_date=(
                    row.movement_date.isoformat()
                    if hasattr(row.movement_date, "isoformat")
                    else str(row.movement_date)
                ),
                movement_type=row.movement_type,
                reference=row.reference or "",
                lot_number=row.lot_number,
                quantity=int(row.quantity),
                unit_cost=float(row.unit_cost) if row.unit_cost else None,
                notes=row.notes,
            )
            for row in rows
        ]

        return MovementsReportDTO(
            medication_id=medication_id,
            generic_name=generic_name,
            items=items,
            total=total,
        )
