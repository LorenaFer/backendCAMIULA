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

import re
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.inventory.infrastructure.repositories.sqlalchemy_report_repository import (
    SQLAlchemyReportRepository,
)
from app.modules.inventory.presentation.schemas.report_schemas import (
    ConsumptionReportResponse,
    EnrichedBatchResponse,
    ExpirationReportResponse,
    InventorySummaryResponse,
    MedicationOptionResponse,
    StockReportResponse,
)
from app.shared.database.session import get_db
from app.shared.middleware.auth import get_current_user_id
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
        "Calcula stock_alert: 'ok' (>50), 'low' (≤50), 'critical' (≤10), 'expired' (0)."
    ),
)
async def get_stock_report(
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    repo = SQLAlchemyReportRepository(session)
    report = await repo.get_stock_report()
    return ok(
        data=StockReportResponse(
            generated_at=report.generated_at,
            items=[i.__dict__ for i in report.items],
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
    repo = SQLAlchemyReportRepository(session)
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
    repo = SQLAlchemyReportRepository(session)
    report = await repo.get_stock_report()

    priority = {"expired": 0, "critical": 1, "low": 2}
    alert_items = [
        i for i in report.items if i.stock_alert in ("low", "critical", "expired")
    ]
    alert_items.sort(key=lambda x: priority.get(x.stock_alert, 99))

    return ok(
        data={
            "generated_at": report.generated_at,
            "items": [i.__dict__ for i in alert_items],
            "total": len(alert_items),
        },
        message=f"{len(alert_items)} medicamentos con stock bajo o crítico",
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
    repo = SQLAlchemyReportRepository(session)
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
    repo = SQLAlchemyReportRepository(session)
    report_90 = await repo.get_expiration_report(threshold_days=90)

    from datetime import date, timedelta

    today = date.today()
    cutoff_30 = today + timedelta(days=30)
    cutoff_60 = today + timedelta(days=60)

    def _to_schema(b) -> dict:
        return _enrich_batch_to_schema(b).model_dump()

    batches_30 = [
        _to_schema(b)
        for b in report_90.batches
        if b.expiration_date <= cutoff_30.isoformat()
    ]
    batches_60 = [
        _to_schema(b)
        for b in report_90.batches
        if cutoff_30.isoformat() < b.expiration_date <= cutoff_60.isoformat()
    ]
    batches_90 = [
        _to_schema(b)
        for b in report_90.batches
        if b.expiration_date > cutoff_60.isoformat()
    ]

    return ok(
        data={
            "generated_at": report_90.generated_at,
            "vencen_en_30": batches_30,
            "vencen_en_60": batches_60,
            "vencen_en_90": batches_90,
            "total": len(report_90.batches),
        },
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
    repo = SQLAlchemyReportRepository(session)
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
    repo = SQLAlchemyReportRepository(session)
    report = await repo.get_movements(
        medication_id=medication_id,
        date_from=date_from,
        date_to=date_to,
        page=page,
        page_size=page_size,
    )
    pages = -(-report.total // page_size) if page_size > 0 else 0
    return ok(
        data={
            "medication_id": report.medication_id,
            "generic_name": report.generic_name,
            "items": [i.__dict__ for i in report.items],
            "pagination": {
                "total": report.total,
                "page": page,
                "page_size": page_size,
                "pages": pages,
            },
        },
        message=f"Movimientos de {report.generic_name}",
    )
