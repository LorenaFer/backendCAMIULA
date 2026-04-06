"""FastAPI routes for the Dashboard BI module."""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.dashboard.presentation.dependencies import get_dashboard_service
from app.modules.dashboard.infrastructure.dashboard_query_service import (
    _parse_date,
    _period_range,
)
from app.modules.dashboard.presentation.schemas.dashboard_schemas import (
    DashboardResponse,
    KpisResponse,
)
from app.shared.database.session import get_db
from app.shared.middleware.auth import get_current_user_id
from app.shared.schemas.responses import ok

router = APIRouter(prefix="/dashboard", tags=["Dashboard BI"])


@router.get("", summary="Consolidated dashboard with KPIs, charts, and trends")
async def get_dashboard(
    fecha: Optional[str] = Query(None, description="Reference date (YYYY-MM-DD)"),
    periodo: Optional[str] = Query(
        "day", description="Period: day | week | month | year"
    ),
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Consolidated dashboard: KPIs, charts, trends. Aggregates cross-module data. Filterable by fecha and periodo."""
    svc = get_dashboard_service(session)
    ref = _parse_date(fecha)
    start, end = _period_range(ref, periodo or "day")

    kpis = await svc.kpis(ref, start, end)
    by_status = await svc.appointments_by_status(start, end)
    by_specialty = await svc.appointments_by_specialty(start, end)
    trend = await svc.daily_trend(ref)
    hourly = await svc.hourly_distribution(start, end)
    heatmap = await svc.heatmap(start, end)
    occupancy = await svc.occupancy_by_specialty(start, end)
    absenteeism = await svc.absenteeism_by_specialty(start, end)
    performance = await svc.performance_by_doctor(start, end)
    by_type = await svc.patients_by_type()
    by_sex = await svc.patients_by_sex()
    first_time, returning = await svc.visit_counts()
    diagnoses = await svc.top_diagnoses(limit=5, start=start, end=end)
    inventory = await svc.inventory_summary()
    consumption = await svc.top_consumption(start, end)

    data = DashboardResponse(
        fecha=ref.isoformat(),
        generated_at=datetime.now(timezone.utc).isoformat(),
        kpis=KpisResponse(**kpis),
        appointments_by_status=by_status,
        appointments_by_specialty=by_specialty,
        daily_trend=trend,
        hourly_distribution=hourly,
        heatmap=heatmap,
        occupancy_by_specialty=occupancy,
        absenteeism_by_specialty=absenteeism,
        performance_by_doctor=performance,
        patients_by_type=by_type,
        patients_by_sex=by_sex,
        first_time_count=first_time,
        returning_count=returning,
        top_diagnoses=diagnoses,
        inventory=inventory,
        top_consumption=consumption,
    )
    return ok(data=data, message="Dashboard generated successfully")
