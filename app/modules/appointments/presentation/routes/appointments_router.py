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
from app.modules.appointments.domain.repositories.appointment_repository import AppointmentRepository
from app.modules.appointments.presentation.dependencies import get_appointment_repo
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
    date_from: str = Query(..., description="Start date YYYY-MM-DD"),
    date_to: str = Query(..., description="End date YYYY-MM-DD"),
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_optional_user_id),
):
    """Appointment frequency heatmap: count per day-of-week and hour. Filter by date range."""
    from datetime import date as _date

    from app.modules.dashboard.infrastructure.dashboard_query_service import (
        DashboardQueryService,
    )

    svc = DashboardQueryService(session)
    heatmap = await svc.heatmap(
        _date.fromisoformat(date_from), _date.fromisoformat(date_to)
    )
    data = {
        "date_from": date_from,
        "date_to": date_to,
        "heatmap": heatmap,
    }
    return ok(data=data, message="Heatmap generated successfully")


@router.get("/stats", summary="Appointment stats")
async def get_stats(
    date_str: Optional[str] = Query(None, description="ISO date YYYY-MM-DD"),
    doctor_id: Optional[str] = Query(None),
    specialty_id: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_optional_user_id),
):
    """Aggregated appointment statistics: counts by status, specialty, doctor, patient type, daily trend, and peak hours."""
    repo = get_appointment_repo(session)
    stats = await GetAppointmentStats(repo).execute(
        date_str=date_str,
        doctor_id=doctor_id,
        specialty_id=specialty_id,
        status_filter=status_filter,
    )
    return ok(data=CitasStats(**stats), message="Estadisticas obtenidas exitosamente")


@router.get("/check-slot", summary="Check if a slot is occupied")
async def check_slot(
    doctor_id: str = Query(...),
    date_str: str = Query(..., description="ISO date YYYY-MM-DD"),
    hora_inicio: str = Query(..., description="HH:MM"),
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_optional_user_id),
):
    """Check if a specific time slot is already occupied. Returns occupied: true/false."""
    repo = get_appointment_repo(session)
    occupied = await CheckSlot(repo).execute(
        doctor_id=doctor_id, date_str=date_str, hora_inicio=hora_inicio
    )
    return ok(
        data=CheckSlotResponse(occupied=occupied),
        message="Disponibilidad verificada",
    )


@router.get("/available-slots", summary="Available time slots for a doctor on a date")
async def get_available_slots(
    doctor_id: str = Query(...),
    date_str: str = Query(..., description="ISO date YYYY-MM-DD"),
    es_nuevo: bool = Query(False, description="True=60min, False=30min"),
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_optional_user_id),
):
    """Compute available time slots for a doctor on a date. Considers availability blocks, exceptions, and existing appointments. Duration: 60min for new patients, 30min for returning."""
    from app.modules.appointments.presentation.dependencies import get_availability_reader
    from app.modules.doctors.domain.repositories.availability_reader import AvailabilityReader

    repo = get_appointment_repo(session)
    reader = get_availability_reader(session)
    slots = await AvailableSlots(repo, reader).execute(
        doctor_id=doctor_id, date_str=date_str, es_nuevo=es_nuevo
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
    """List dates with availability in a given month. Excludes weekends, past dates, days without blocks, and days with exceptions."""
    from app.modules.appointments.presentation.dependencies import get_availability_reader

    reader = get_availability_reader(session)
    dates = await AvailableDates(reader).execute(
        doctor_id=doctor_id, year=year, month=month
    )
    return ok(data=dates, message="Fechas disponibles obtenidas")


@router.get("/{appointment_id}", summary="Get appointment detail")
async def get_appointment(
    appointment_id: str,
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_optional_user_id),
):
    """Retrieve full appointment details including patient name, doctor name, and specialty."""
    repo = get_appointment_repo(session)
    appointment = await GetAppointment(repo).execute(appointment_id)
    return ok(
        data=AppointmentResponse(**appointment.__dict__),
        message="Cita obtenida exitosamente",
    )


@router.get("", summary="List appointments (paginated, filtered)")
async def list_appointments(
    date_str: Optional[str] = Query(None, description="ISO date YYYY-MM-DD"),
    doctor_id: Optional[str] = Query(None),
    specialty_id: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None),
    q: Optional[str] = Query(None, description="Search patient name/dni"),
    fk_patient_id: Optional[str] = Query(None, description="Filter by patient ID"),
    month_str: Optional[str] = Query(None, description="YYYY-MM for month view"),
    exclude_cancelled: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=10000),
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_optional_user_id),
):
    """List appointments with multiple view modes: doctor month view, doctor day view, or general list with search and pagination."""
    repo = get_appointment_repo(session)

    # Doctor month view: GET /appointments?doctor_id=X&month_str=YYYY-MM&exclude_cancelled=true
    if doctor_id and month_str:
        parts = month_str.split("-")
        year, month = int(parts[0]), int(parts[1])
        items = await ListDoctorMonthAppointments(repo).execute(
            doctor_id=doctor_id,
            year=year,
            month=month,
            exclude_cancelled=exclude_cancelled,
        )
        data = [AppointmentResponse(**a.__dict__) for a in items]
        return ok(data=data, message="Citas del month_str obtenidas exitosamente")

    # Doctor day view: GET /appointments?doctor_id=X&fecha=X&exclude_cancelled=true
    if doctor_id and date_str and exclude_cancelled:
        items = await ListDoctorDayAppointments(repo).execute(
            doctor_id=doctor_id,
            date_str=date_str,
            exclude_cancelled=exclude_cancelled,
        )
        data = [AppointmentResponse(**a.__dict__) for a in items]
        return ok(data=data, message="Citas del dia obtenidas exitosamente")

    # General paginated list
    items, total = await ListAppointments(repo).execute(
        page=page,
        page_size=page_size,
        date_str=date_str,
        doctor_id=doctor_id,
        specialty_id=specialty_id,
        status_filter=status_filter,
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
    """Create a new appointment. Validates no double-booking using SELECT FOR UPDATE."""
    repo = get_appointment_repo(session)
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
    """Transition an appointment through the state machine. Valid: pendiente -> confirmada/cancelada/atendida/no_asistio, confirmada -> atendida/cancelada/no_asistio."""
    repo = get_appointment_repo(session)
    appointment = await UpdateAppointmentStatus(repo).execute(
        appointment_id=appointment_id,
        new_status=body.new_status,
        updated_by=user_id,
    )
    return ok(
        data=AppointmentResponse(**appointment.__dict__),
        message="Estado de cita actualizado exitosamente",
    )
