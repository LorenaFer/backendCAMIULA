"""FastAPI routes for the Appointment resource."""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.appointments.application.dtos.appointment_dto import (
    CreateAppointmentDTO,
)
from app.modules.appointments.application.use_cases.available_dates import (
    AvailableDates,
)
from app.modules.appointments.application.use_cases.available_slots import (
    AvailableSlots,
)
from app.modules.appointments.application.use_cases.check_slot import CheckSlot
from app.modules.appointments.application.use_cases.create_appointment import (
    CreateAppointment,
)
from app.modules.appointments.application.use_cases.get_appointment import (
    GetAppointment,
)
from app.modules.appointments.application.use_cases.get_stats import (
    GetAppointmentStats,
)
from app.modules.appointments.application.use_cases.list_appointments import (
    ListAppointments,
    ListDoctorDayAppointments,
    ListDoctorMonthAppointments,
)
from app.modules.appointments.application.use_cases.update_status import (
    UpdateAppointmentStatus,
)
from app.modules.appointments.infrastructure.repositories.sqlalchemy_appointment_repository import (
    SQLAlchemyAppointmentRepository,
)
from app.modules.appointments.presentation.schemas.appointment_schemas import (
    AppointmentCreate,
    AppointmentResponse,
    AppointmentStatusUpdate,
    CheckSlotResponse,
    CitasStats,
    SlotResponse,
)
from app.shared.database.session import get_db
from app.shared.middleware.auth import get_current_user_id, get_optional_user_id
from app.shared.schemas.responses import created, ok, paginated

router = APIRouter(prefix="/appointments", tags=["Appointments"])


# ── Static routes first (before {id} params) ──────────────────


@router.get("/heatmap", summary="Appointments heatmap (day x hour)")
async def get_heatmap(
    fecha_desde: str = Query(..., description="Start date YYYY-MM-DD"),
    fecha_hasta: str = Query(..., description="End date YYYY-MM-DD"),
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_optional_user_id),
):
    from datetime import date as _date

    from app.modules.dashboard.infrastructure.dashboard_query_service import (
        DashboardQueryService,
    )

    svc = DashboardQueryService(session)
    heatmap = await svc.heatmap(
        _date.fromisoformat(fecha_desde), _date.fromisoformat(fecha_hasta)
    )
    data = {
        "fecha_desde": fecha_desde,
        "fecha_hasta": fecha_hasta,
        "heatmap": heatmap,
    }
    return ok(data=data, message="Heatmap generated successfully")


@router.get("/stats", summary="Appointment stats")
async def get_stats(
    fecha: Optional[str] = Query(None, description="ISO date YYYY-MM-DD"),
    doctor_id: Optional[str] = Query(None),
    especialidad_id: Optional[str] = Query(None),
    estado: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_optional_user_id),
):
    repo = SQLAlchemyAppointmentRepository(session)
    stats = await GetAppointmentStats(repo).execute(
        fecha=fecha,
        doctor_id=doctor_id,
        especialidad_id=especialidad_id,
        estado=estado,
    )
    return ok(data=CitasStats(**stats), message="Estadisticas obtenidas exitosamente")


@router.get("/check-slot", summary="Check if a slot is occupied")
async def check_slot(
    doctor_id: str = Query(...),
    fecha: str = Query(..., description="ISO date YYYY-MM-DD"),
    hora_inicio: str = Query(..., description="HH:MM"),
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_optional_user_id),
):
    repo = SQLAlchemyAppointmentRepository(session)
    occupied = await CheckSlot(repo).execute(
        doctor_id=doctor_id, fecha=fecha, hora_inicio=hora_inicio
    )
    return ok(
        data=CheckSlotResponse(occupied=occupied),
        message="Disponibilidad verificada",
    )


@router.get("/available-slots", summary="Available time slots for a doctor on a date")
async def get_available_slots(
    doctor_id: str = Query(...),
    fecha: str = Query(..., description="ISO date YYYY-MM-DD"),
    es_nuevo: bool = Query(False, description="True=60min, False=30min"),
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_optional_user_id),
):
    repo = SQLAlchemyAppointmentRepository(session)
    slots = await AvailableSlots(repo, session).execute(
        doctor_id=doctor_id, fecha=fecha, es_nuevo=es_nuevo
    )
    data = [SlotResponse(**s) for s in slots]
    return ok(data=data, message="Slots disponibles obtenidos")


@router.get("/available-dates", summary="Dates with availability in a month")
async def get_available_dates(
    doctor_id: str = Query(...),
    year: int = Query(...),
    month: int = Query(..., ge=1, le=12),
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_optional_user_id),
):
    dates = await AvailableDates(session).execute(
        doctor_id=doctor_id, year=year, month=month
    )
    return ok(data=dates, message="Fechas disponibles obtenidas")


@router.get("/{appointment_id}", summary="Get appointment detail")
async def get_appointment(
    appointment_id: str,
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_optional_user_id),
):
    repo = SQLAlchemyAppointmentRepository(session)
    appointment = await GetAppointment(repo).execute(appointment_id)
    return ok(
        data=AppointmentResponse(**appointment.__dict__),
        message="Cita obtenida exitosamente",
    )


@router.get("", summary="List appointments (paginated, filtered)")
async def list_appointments(
    fecha: Optional[str] = Query(None, description="ISO date YYYY-MM-DD"),
    doctor_id: Optional[str] = Query(None),
    especialidad_id: Optional[str] = Query(None),
    estado: Optional[str] = Query(None),
    q: Optional[str] = Query(None, description="Search patient name/cedula"),
    fk_patient_id: Optional[str] = Query(None, description="Filter by patient ID"),
    mes: Optional[str] = Query(None, description="YYYY-MM for month view"),
    excluir_canceladas: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_optional_user_id),
):
    repo = SQLAlchemyAppointmentRepository(session)

    # Doctor month view: GET /appointments?doctor_id=X&mes=YYYY-MM&excluir_canceladas=true
    if doctor_id and mes:
        parts = mes.split("-")
        year, month = int(parts[0]), int(parts[1])
        items = await ListDoctorMonthAppointments(repo).execute(
            doctor_id=doctor_id,
            year=year,
            month=month,
            exclude_cancelled=excluir_canceladas,
        )
        data = [AppointmentResponse(**a.__dict__) for a in items]
        return ok(data=data, message="Citas del mes obtenidas exitosamente")

    # Doctor day view: GET /appointments?doctor_id=X&fecha=X&excluir_canceladas=true
    if doctor_id and fecha and excluir_canceladas:
        items = await ListDoctorDayAppointments(repo).execute(
            doctor_id=doctor_id,
            fecha=fecha,
            exclude_cancelled=excluir_canceladas,
        )
        data = [AppointmentResponse(**a.__dict__) for a in items]
        return ok(data=data, message="Citas del dia obtenidas exitosamente")

    # General paginated list
    items, total = await ListAppointments(repo).execute(
        page=page,
        page_size=page_size,
        fecha=fecha,
        doctor_id=doctor_id,
        especialidad_id=especialidad_id,
        estado=estado,
        q=q,
        fk_patient_id=fk_patient_id,
    )
    data = [AppointmentResponse(**a.__dict__) for a in items]
    return paginated(data, total, page, page_size, "Citas obtenidas exitosamente")


@router.post("", summary="Create appointment", status_code=201)
async def create_appointment(
    body: AppointmentCreate,
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_optional_user_id),
):
    repo = SQLAlchemyAppointmentRepository(session)
    dto = CreateAppointmentDTO(**body.model_dump())
    appointment = await CreateAppointment(repo).execute(dto, created_by=user_id)
    return created(
        data=AppointmentResponse(**appointment.__dict__),
        message="Cita creada exitosamente",
    )


@router.patch("/{appointment_id}/status", summary="Update appointment status")
async def update_appointment_status(
    appointment_id: str,
    body: AppointmentStatusUpdate,
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_optional_user_id),
):
    repo = SQLAlchemyAppointmentRepository(session)
    appointment = await UpdateAppointmentStatus(repo).execute(
        appointment_id=appointment_id,
        new_status=body.new_status,
        updated_by=user_id,
    )
    return ok(
        data=AppointmentResponse(**appointment.__dict__),
        message="Estado de cita actualizado exitosamente",
    )
