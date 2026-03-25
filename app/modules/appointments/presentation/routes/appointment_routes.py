from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.appointments.application.dtos.appointment_dto import (
    ChangeAppointmentStatusDTO,
    CreateAppointmentDTO,
)
from app.modules.appointments.application.use_cases.change_appointment_status import (
    ChangeAppointmentStatusUseCase,
)
from app.modules.appointments.application.use_cases.check_slot_availability import (
    CheckSlotAvailabilityUseCase,
)
from app.modules.appointments.application.use_cases.create_appointment import (
    CreateAppointmentUseCase,
)
from app.modules.appointments.application.use_cases.get_appointment_detail import (
    GetAppointmentDetailUseCase,
)
from app.modules.appointments.application.use_cases.list_appointments import (
    ListAppointmentsUseCase,
)
from app.modules.appointments.infrastructure.repositories.sqlalchemy_appointment_repository import (
    SQLAlchemyAppointmentRepository,
)
from app.modules.appointments.infrastructure.repositories.sqlalchemy_availability_repository import (
    SQLAlchemyAvailabilityRepository,
)
from app.modules.appointments.presentation.schemas.appointment_schema import (
    AppointmentResponse,
    ChangeStatusRequest,
    CheckSlotResponse,
    CreateAppointmentRequest,
    DoctorInAppointment,
    PatientInAppointment,
)
from app.modules.appointments.presentation.utils import parse_time
from app.shared.database.session import get_db
from app.shared.middleware.auth import require_permission
from app.shared.schemas.responses import created, ok, paginated

router = APIRouter(prefix="/appointments", tags=["Appointments"])


def _to_response(apt) -> dict:
    resp = AppointmentResponse(
        id=apt.id,
        paciente_id=apt.patient_id,
        doctor_id=apt.doctor_id,
        especialidad_id=apt.specialty_id,
        fecha=apt.appointment_date,
        hora_inicio=apt.start_time.strftime("%H:%M"),
        hora_fin=apt.end_time.strftime("%H:%M"),
        duracion_min=apt.duration_minutes,
        es_primera_vez=apt.is_first_visit,
        estado=apt.appointment_status.lower(),
        motivo_consulta=apt.reason,
        observaciones=apt.observations,
        created_at=apt.created_at,
        created_by=apt.created_by,
        paciente=PatientInAppointment(**apt.patient_data) if apt.patient_data else None,
        doctor=DoctorInAppointment(**apt.doctor_data) if apt.doctor_data else None,
    )
    return resp.model_dump()


@router.post("", status_code=201)
async def create_appointment(
    body: CreateAppointmentRequest,
    user=Depends(require_permission("appointments:create")),
    db: AsyncSession = Depends(get_db),
):
    """Crear una nueva cita."""
    apt_repo = SQLAlchemyAppointmentRepository(db)
    avail_repo = SQLAlchemyAvailabilityRepository(db)
    use_case = CreateAppointmentUseCase(
        appointment_repo=apt_repo,
        availability_repo=avail_repo,
    )
    appointment = await use_case.execute(
        CreateAppointmentDTO(
            patient_id=body.paciente_id,
            doctor_id=body.doctor_id,
            specialty_id=body.especialidad_id,
            appointment_date=body.fecha,
            start_time=parse_time(body.hora_inicio),
            end_time=parse_time(body.hora_fin),
            duration_minutes=body.duracion_min,
            is_first_visit=body.es_primera_vez,
            reason=body.motivo_consulta,
            observations=body.observaciones,
        ),
        created_by=user.id,
    )
    return created(data=_to_response(appointment), message="Cita creada exitosamente")


@router.get("")
async def list_appointments(
    fecha: Optional[date] = Query(None),
    doctor_id: Optional[str] = Query(None),
    especialidad_id: Optional[str] = Query(None),
    estado: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    mes: Optional[str] = Query(None),
    excluir_canceladas: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    _=Depends(require_permission("appointments:read")),
    db: AsyncSession = Depends(get_db),
):
    """Listar citas con filtros y paginación."""
    repo = SQLAlchemyAppointmentRepository(db)
    use_case = ListAppointmentsUseCase(appointment_repo=repo)
    items, total = await use_case.execute(
        page=page,
        page_size=page_size,
        fecha=fecha,
        doctor_id=doctor_id,
        specialty_id=especialidad_id,
        estado=estado,
        q=q,
        mes=mes,
        excluir_canceladas=excluir_canceladas,
    )
    return paginated(
        items=[_to_response(apt) for apt in items],
        total=total,
        page=page,
        page_size=page_size,
        message="Listado de citas",
    )


@router.get("/check-slot")
async def check_slot(
    doctor_id: str = Query(...),
    fecha: date = Query(...),
    hora_inicio: str = Query(...),
    _=Depends(require_permission("appointments:read")),
    db: AsyncSession = Depends(get_db),
):
    """Verificar si un slot está disponible."""
    repo = SQLAlchemyAppointmentRepository(db)
    use_case = CheckSlotAvailabilityUseCase(appointment_repo=repo)
    occupied = await use_case.execute(
        doctor_id=doctor_id,
        appointment_date=fecha,
        start_time=parse_time(hora_inicio),
    )
    return ok(
        data=CheckSlotResponse(ocupado=occupied).model_dump(),
        message="Verificación de slot",
    )


@router.get("/{appointment_id}")
async def get_appointment(
    appointment_id: str,
    _=Depends(require_permission("appointments:read")),
    db: AsyncSession = Depends(get_db),
):
    """Detalle de una cita con datos de paciente y doctor."""
    repo = SQLAlchemyAppointmentRepository(db)
    use_case = GetAppointmentDetailUseCase(appointment_repo=repo)
    appointment = await use_case.execute(appointment_id)
    return ok(data=_to_response(appointment), message="Detalle de la cita")


@router.patch("/{appointment_id}/status")
async def change_status(
    appointment_id: str,
    body: ChangeStatusRequest,
    user=Depends(require_permission("appointments:update")),
    db: AsyncSession = Depends(get_db),
):
    """Cambiar el estado de una cita."""
    repo = SQLAlchemyAppointmentRepository(db)
    use_case = ChangeAppointmentStatusUseCase(appointment_repo=repo)
    status_map = {
        "pendiente": "PENDING",
        "confirmada": "CONFIRMED",
        "atendida": "ATTENDED",
        "cancelada": "CANCELLED",
        "no_asistio": "NO_SHOW",
    }
    new_status = status_map.get(body.estado.lower(), body.estado.upper())
    await use_case.execute(
        ChangeAppointmentStatusDTO(
            appointment_id=appointment_id,
            new_status=new_status,
        ),
        updated_by=user.id,
    )
    return ok(message="Estado actualizado")
