"""Rutas FastAPI para reportes de inventario.

Todos los endpoints son de solo lectura (GET).
Se utiliza SQLAlchemyReportRepository para las consultas de agregación.

Endpoints:
    GET /reports/stock               — Reporte completo de stock (dashboard principal)
    GET /reports/inventory-summary   — KPIs ejecutivos del dashboard
    GET /reports/low-stock           — Medicamentos con stock bajo o crítico
    GET /reports/expiration          — Lotes próximos a vencer (usado por frontend)
    GET /reports/expiring-soon       — Alias semántico de /expiration con 3 horizontes
    GET /reports/consumption         — Consumo mensual por medicamento
    GET /reports/movements           — Kardex paginado (entradas + salidas)
"""

from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.inventory.presentation.dependencies import get_movement_repo, get_report_repo
from app.modules.inventory.presentation.schemas.report_schemas import (
    ConsumptionReportResponse,
    EnrichedBatchResponse,
    ExpirationReportResponse,
    ExpiringSoonReportResponse,
    InventoryMovementResponse,
    InventoryMovementsListResponse,
    InventorySummaryResponse,
    LowStockReportResponse,
    MedicationOptionResponse,
    MovementItemResponse,
    MovementsReportResponse,
    PaginationMeta,
    StockAlertResponse,
    StockAlertsListResponse,
    StockItemResponse,
    StockReportResponse,
)
from app.shared.database.session import get_db
from app.shared.middleware.auth import get_optional_user_id as get_current_user_id
from app.shared.schemas.responses import ok

router = APIRouter(prefix="/reports", tags=["Inventory — Reports"])


# ──────────────────────────────────────────────────────────
# Helpers de conversión DTO → Schema
# ──────────────────────────────────────────────────────────

def _enrich_batch_to_schema(b) -> EnrichedBatchResponse:
    med = MedicationOptionResponse(
        id=b.medication.id,
        code=b.medication.code,
        generic_name=b.medication.generic_name,
        pharmaceutical_form=b.medication.pharmaceutical_form,
        unit_measure=b.medication.unit_measure,
        current_stock=b.medication.current_stock,
    )
    return EnrichedBatchResponse(
        id=b.id,
        fk_medication_id=b.fk_medication_id,
        medication=med,
        fk_supplier_id=b.fk_supplier_id,
        supplier_name=b.supplier_name,
        lot_number=b.lot_number,
        expiration_date=b.expiration_date,
        quantity_received=b.quantity_received,
        quantity_available=b.quantity_available,
        unit_cost=b.unit_cost,
        batch_status=b.batch_status,
        received_at=b.received_at,
    )


# ──────────────────────────────────────────────────────────
# Reporte principal de stock (usado por el dashboard)
# ──────────────────────────────────────────────────────────

@router.get(
    "/stock",
    summary="Reporte completo de stock por medicamento",
    description=(
        "Consolida el inventario disponible por medicamento. "
        "Solo incluye lotes con batch_status='available' y expiration_date >= hoy. "
        "Calcula stock_alert: 'ok' (>50), 'low' (≤50), 'critical' (≤10), 'expired' (0). "
        "Auto-generates stock alerts for medications crossing thresholds."
    ),
)
async def get_stock_report(
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    repo = get_report_repo(session)
    report = await repo.get_stock_report()

    # Auto-generate stock alerts on each stock report request
    movement_repo = get_movement_repo(session)
    await movement_repo.generate_alerts(created_by=user_id)

    return ok(
        data=StockReportResponse(
            generated_at=report.generated_at,
            items=[StockItemResponse(**i.__dict__) for i in report.items],
            total_medications=report.total_medications,
            critical_count=report.critical_count,
            expired_count=report.expired_count,
        ),
        message="Reporte de stock generado exitosamente",
    )


# ──────────────────────────────────────────────────────────
# KPIs ejecutivos
# ──────────────────────────────────────────────────────────

@router.get(
    "/inventory-summary",
    summary="KPIs ejecutivos del inventario",
    description=(
        "Resumen para el panel de control: total de SKUs activos, "
        "conteo por nivel de alerta y unidades disponibles totales."
    ),
)
async def get_inventory_summary(
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    repo = get_report_repo(session)
    summary = await repo.get_inventory_summary()
    return ok(
        data=InventorySummaryResponse(**summary.__dict__),
        message="Resumen de inventario generado exitosamente",
    )


# ──────────────────────────────────────────────────────────
# Stock bajo / crítico
# ──────────────────────────────────────────────────────────

@router.get(
    "/low-stock",
    summary="Medicamentos con stock bajo o crítico",
    description=(
        "Filtra el reporte de stock retornando únicamente los medicamentos "
        "con stock_alert en 'low', 'critical' o 'expired'. "
        "Ordenados por criticidad (expired → critical → low)."
    ),
)
async def get_low_stock(
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    repo = get_report_repo(session)
    report = await repo.get_low_stock_report()
    return ok(
        data=LowStockReportResponse(
            generated_at=report.generated_at,
            items=[StockItemResponse(**i.__dict__) for i in report.items],
            total=len(report.items),
        ),
        message=f"{len(report.items)} medicamentos con stock bajo o crítico",
    )


# ──────────────────────────────────────────────────────────
# Próximos a vencer (endpoint primario para el frontend)
# ──────────────────────────────────────────────────────────

@router.get(
    "/expiration",
    summary="Lotes próximos a vencer",
    description=(
        "Devuelve los lotes disponibles cuya expiration_date está dentro del "
        "horizonte indicado en threshold_days (por defecto 90 días). "
        "Cada lote incluye datos del medicamento en el campo 'medication'."
    ),
)
async def get_expiration_report(
    threshold_days: int = Query(
        90, ge=1, le=365, description="Días a partir de hoy como horizonte de búsqueda"
    ),
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    repo = get_report_repo(session)
    report = await repo.get_expiration_report(threshold_days)
    return ok(
        data=ExpirationReportResponse(
            generated_at=report.generated_at,
            threshold_days=report.threshold_days,
            batches=[_enrich_batch_to_schema(b) for b in report.batches],
        ),
        message=f"Lotes que vencen en los próximos {threshold_days} días",
    )


# ──────────────────────────────────────────────────────────
# Próximos a vencer con horizontes 30 / 60 / 90
# ──────────────────────────────────────────────────────────

@router.get(
    "/expiring-soon",
    summary="Lotes próximos a vencer agrupados en horizontes 30/60/90 días",
    description=(
        "Extiende /expiration clasificando los lotes en tres grupos: "
        "vencen_en_30, vencen_en_60 y vencen_en_90 días. "
        "Útil para planificación de reposición."
    ),
)
async def get_expiring_soon(
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    repo = get_report_repo(session)
    report_90 = await repo.get_expiration_report(threshold_days=90)

    today = date.today()
    cutoff_30 = today + timedelta(days=30)
    cutoff_60 = today + timedelta(days=60)

    batches_30: list[EnrichedBatchResponse] = []
    batches_60: list[EnrichedBatchResponse] = []
    batches_90: list[EnrichedBatchResponse] = []

    for b in report_90.batches:
        exp = date.fromisoformat(b.expiration_date) if isinstance(b.expiration_date, str) else b.expiration_date
        schema = _enrich_batch_to_schema(b)
        if exp <= cutoff_30:
            batches_30.append(schema)
        elif exp <= cutoff_60:
            batches_60.append(schema)
        else:
            batches_90.append(schema)

    return ok(
        data=ExpiringSoonReportResponse(
            generated_at=report_90.generated_at,
            vencen_en_30=batches_30,
            vencen_en_60=batches_60,
            vencen_en_90=batches_90,
            total=len(report_90.batches),
        ),
        message="Lotes próximos a vencer agrupados por horizonte",
    )


# ──────────────────────────────────────────────────────────
# Consumo mensual
# ──────────────────────────────────────────────────────────

@router.get(
    "/consumption",
    summary="Reporte de consumo mensual por medicamento",
    description=(
        "Agrega los despachos completados en el período indicado (YYYY-MM). "
        "Devuelve total despachado, número de despachos y pacientes distintos "
        "para cada medicamento."
    ),
)
async def get_consumption_report(
    period: str = Query(
        ...,
        description="Mes en formato YYYY-MM (ej. 2026-03)",
        pattern=r"^\d{4}-(?:0[1-9]|1[0-2])$",
    ),
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    repo = get_report_repo(session)
    report = await repo.get_consumption_report(period)
    return ok(
        data=ConsumptionReportResponse(
            period=report.period,
            items=[i.__dict__ for i in report.items],
        ),
        message=f"Consumo del período {period} generado exitosamente",
    )


# ──────────────────────────────────────────────────────────
# Kardex / Movimientos
# ──────────────────────────────────────────────────────────

@router.get(
    "/movements",
    summary="Kardex paginado de un medicamento (entradas + salidas)",
    description=(
        "Combina entradas (lotes recibidos de órdenes de compra) y "
        "salidas (ítems despachados) de un medicamento en orden cronológico "
        "inverso. Soporta filtros de fecha y paginación."
    ),
)
async def get_movements(
    medication_id: str = Query(..., description="ID del medicamento"),
    date_from: Optional[str] = Query(
        None, description="Fecha inicio ISO YYYY-MM-DD (inclusive)"
    ),
    date_to: Optional[str] = Query(
        None, description="Fecha fin ISO YYYY-MM-DD (inclusive)"
    ),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    repo = get_report_repo(session)
    report = await repo.get_movements(
        medication_id=medication_id,
        date_from=date_from,
        date_to=date_to,
        page=page,
        page_size=page_size,
    )
    pages = -(-report.total // page_size) if page_size > 0 else 0
    return ok(
        data=MovementsReportResponse(
            medication_id=report.medication_id,
            generic_name=report.generic_name,
            items=[MovementItemResponse(**i.__dict__) for i in report.items],
            pagination=PaginationMeta(
                total=report.total,
                page=page,
                page_size=page_size,
                pages=pages,
            ),
        ),
        message=f"Movimientos de {report.generic_name}",
    )


# ──────────────────────────────────────────────────────────
# Inventory Movements (trazabilidad persistida)
# ──────────────────────────────────────────────────────────

@router.get(
    "/inventory-movements",
    summary="Movimientos de inventario persistidos (trazabilidad)",
    description=(
        "Lista paginada de todos los movimientos de inventario registrados. "
        "Cada entrada/salida/ajuste/expiración queda persistida con tipo, "
        "cantidad, balance resultante y referencia al origen."
    ),
)
async def get_inventory_movements(
    medication_id: Optional[str] = Query(None, description="Filter by medication ID"),
    movement_type: Optional[str] = Query(
        None, description="Filter by type: entry, exit, adjustment, expiration"
    ),
    date_from: Optional[str] = Query(None, description="Start date ISO YYYY-MM-DD"),
    date_to: Optional[str] = Query(None, description="End date ISO YYYY-MM-DD"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    repo = get_movement_repo(session)
    result = await repo.get_movements(
        medication_id=medication_id,
        movement_type=movement_type,
        date_from=date_from,
        date_to=date_to,
        page=page,
        page_size=page_size,
    )
    pages = -(-result.total // page_size) if page_size > 0 else 0
    return ok(
        data=InventoryMovementsListResponse(
            items=[InventoryMovementResponse(**i.__dict__) for i in result.items],
            pagination=PaginationMeta(
                total=result.total,
                page=page,
                page_size=page_size,
                pages=pages,
            ),
        ),
        message=f"{result.total} movimientos encontrados",
    )


# ──────────────────────────────────────────────────────────
# Stock Alerts (alertas persistidas)
# ──────────────────────────────────────────────────────────

@router.get(
    "/stock-alerts",
    summary="Alertas de stock persistidas",
    description=(
        "Lista paginada de alertas de stock. Cada alerta registra cuando un "
        "medicamento cruza un umbral (low, critical, expired). Las alertas "
        "se resuelven automáticamente al reponer stock o manualmente."
    ),
)
async def get_stock_alerts(
    alert_status: Optional[str] = Query(
        None, description="Filter: active, resolved, acknowledged"
    ),
    alert_level: Optional[str] = Query(
        None, description="Filter: low, critical, expired"
    ),
    medication_id: Optional[str] = Query(None, description="Filter by medication ID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    repo = get_movement_repo(session)
    result = await repo.get_alerts(
        alert_status=alert_status,
        alert_level=alert_level,
        medication_id=medication_id,
        page=page,
        page_size=page_size,
    )
    return ok(
        data=StockAlertsListResponse(
            items=[StockAlertResponse(**i.__dict__) for i in result.items],
            total=result.total,
            active_count=result.active_count,
            resolved_count=result.resolved_count,
        ),
        message=f"{result.total} alertas encontradas ({result.active_count} activas)",
    )


@router.post(
    "/stock-alerts/generate",
    summary="Generar alertas de stock",
    description=(
        "Escanea todos los medicamentos activos y genera alertas para aquellos "
        "que han cruzado los umbrales de stock (low <= 50, critical <= 10, "
        "expired = 0). Auto-resuelve alertas previas si el stock se recupera."
    ),
)
async def generate_stock_alerts(
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    repo = get_movement_repo(session)
    new_count = await repo.generate_alerts(created_by=user_id)
    await session.commit()
    return ok(
        data={"new_alerts": new_count},
        message=f"{new_count} nuevas alertas generadas",
    )


@router.patch(
    "/stock-alerts/{alert_id}/acknowledge",
    summary="Marcar alerta como reconocida",
)
async def acknowledge_alert(
    alert_id: str,
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    repo = get_movement_repo(session)
    success = await repo.acknowledge_alert(alert_id, user_id)
    if not success:
        from app.core.exceptions import AppException
        raise AppException(status_code=404, message="Alert not found or already resolved")
    await session.commit()
    return ok(message="Alert acknowledged")


@router.patch(
    "/stock-alerts/{alert_id}/resolve",
    summary="Resolver alerta manualmente",
)
async def resolve_alert(
    alert_id: str,
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    repo = get_movement_repo(session)
    success = await repo.resolve_alert(alert_id, user_id)
    if not success:
        from app.core.exceptions import AppException
        raise AppException(status_code=404, message="Alert not found or already resolved")
    await session.commit()
    return ok(message="Alert resolved")
