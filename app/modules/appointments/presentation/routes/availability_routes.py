from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.appointments.application.dtos.availability_dto import (
    CreateAvailabilityBlockDTO,
    UpdateAvailabilityBlockDTO,
)
from app.modules.appointments.application.use_cases.check_doctor_exception import (
    CheckDoctorExceptionUseCase,
)
from app.modules.appointments.application.use_cases.create_availability_block import (
    CreateAvailabilityBlockUseCase,
)
from app.modules.appointments.application.use_cases.delete_availability_block import (
    DeleteAvailabilityBlockUseCase,
)
from app.modules.appointments.application.use_cases.list_availability_blocks import (
    ListAvailabilityBlocksUseCase,
)
from app.modules.appointments.application.use_cases.update_availability_block import (
    UpdateAvailabilityBlockUseCase,
)
from app.modules.appointments.infrastructure.repositories.sqlalchemy_availability_repository import (
    SQLAlchemyAvailabilityRepository,
)
from app.modules.appointments.presentation.schemas.availability_schema import (
    AvailabilityBlockResponse,
    CreateAvailabilityBlockRequest,
    ExceptionCheckResponse,
    UpdateAvailabilityBlockRequest,
)
from app.modules.appointments.presentation.utils import parse_time
from app.shared.database.session import get_db
from app.shared.middleware.auth import require_permission
from app.shared.schemas.responses import created, ok

router = APIRouter(prefix="/doctors", tags=["Doctor Availability"])


def _block_response(b) -> dict:
    return AvailabilityBlockResponse(
        id=b.id,
        doctor_id=b.doctor_id,
        day_of_week=b.day_of_week,
        hora_inicio=b.start_time.strftime("%H:%M"),
        hora_fin=b.end_time.strftime("%H:%M"),
        duracion_slot=b.slot_duration,
    ).model_dump()


@router.get("/{doctor_id}/availability")
async def list_availability(
    doctor_id: str,
    dow: int = Query(None, ge=1, le=5),
    _=Depends(require_permission("doctors:read")),
    db: AsyncSession = Depends(get_db),
):
    """Bloques de disponibilidad de un doctor."""
    repo = SQLAlchemyAvailabilityRepository(db)
    use_case = ListAvailabilityBlocksUseCase(availability_repo=repo)
    blocks = await use_case.execute(doctor_id, day_of_week=dow)
    return ok(data=[_block_response(b) for b in blocks], message="Bloques de disponibilidad")


@router.post("/{doctor_id}/availability", status_code=201)
async def create_availability(
    doctor_id: str,
    body: CreateAvailabilityBlockRequest,
    user=Depends(require_permission("doctors:availability")),
    db: AsyncSession = Depends(get_db),
):
    """Crear bloque de disponibilidad."""
    repo = SQLAlchemyAvailabilityRepository(db)
    use_case = CreateAvailabilityBlockUseCase(availability_repo=repo)
    block = await use_case.execute(
        CreateAvailabilityBlockDTO(
            doctor_id=doctor_id,
            day_of_week=body.day_of_week,
            start_time=parse_time(body.hora_inicio),
            end_time=parse_time(body.hora_fin),
            slot_duration=body.duracion_slot,
        )
    )
    return created(data=_block_response(block), message="Bloque creado")


@router.patch("/{doctor_id}/availability/{block_id}")
async def update_availability(
    doctor_id: str,
    block_id: str,
    body: UpdateAvailabilityBlockRequest,
    user=Depends(require_permission("doctors:availability")),
    db: AsyncSession = Depends(get_db),
):
    """Modificar horas de un bloque."""
    repo = SQLAlchemyAvailabilityRepository(db)
    use_case = UpdateAvailabilityBlockUseCase(availability_repo=repo)
    await use_case.execute(
        UpdateAvailabilityBlockDTO(
            block_id=block_id,
            start_time=parse_time(body.hora_inicio) if body.hora_inicio else None,
            end_time=parse_time(body.hora_fin) if body.hora_fin else None,
        )
    )
    return ok(message="Bloque actualizado")


@router.delete("/{doctor_id}/availability/{block_id}", status_code=200)
async def delete_availability(
    doctor_id: str,
    block_id: str,
    user=Depends(require_permission("doctors:availability")),
    db: AsyncSession = Depends(get_db),
):
    """Eliminar bloque de disponibilidad (soft-delete)."""
    repo = SQLAlchemyAvailabilityRepository(db)
    use_case = DeleteAvailabilityBlockUseCase(availability_repo=repo)
    await use_case.execute(block_id, deleted_by=user.id)
    return ok(message="Bloque eliminado")


@router.get("/{doctor_id}/exceptions")
async def check_exception(
    doctor_id: str,
    fecha: date = Query(..., alias="date"),
    _=Depends(require_permission("doctors:read")),
    db: AsyncSession = Depends(get_db),
):
    """Verificar si el doctor tiene excepción en una fecha."""
    repo = SQLAlchemyAvailabilityRepository(db)
    use_case = CheckDoctorExceptionUseCase(availability_repo=repo)
    has_exc = await use_case.execute(doctor_id, fecha)
    return ok(
        data=ExceptionCheckResponse(excepcion=has_exc).model_dump(),
        message="Verificación de excepción",
    )
