"""FastAPI routes for Doctor Availability and Exceptions."""

from typing import Optional

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.doctors.application.dtos.availability_dto import (
    CreateAvailabilityDTO,
    UpdateAvailabilityDTO,
)
from app.modules.doctors.application.use_cases.availability.create_availability import (
    CreateAvailability,
)
from app.modules.doctors.application.use_cases.availability.delete_availability import (
    DeleteAvailability,
)
from app.modules.doctors.application.use_cases.availability.get_availability import (
    GetAvailability,
)
from app.modules.doctors.application.use_cases.availability.update_availability import (
    UpdateAvailability,
)
from app.modules.doctors.application.use_cases.exceptions.get_exceptions import (
    GetExceptions,
)
from app.modules.doctors.infrastructure.repositories.sqlalchemy_availability_repository import (
    SQLAlchemyAvailabilityRepository,
)
from app.modules.doctors.infrastructure.repositories.sqlalchemy_exception_repository import (
    SQLAlchemyExceptionRepository,
)
from app.modules.doctors.presentation.schemas.availability_schemas import (
    AvailabilityCreate,
    AvailabilityResponse,
    AvailabilityUpdate,
    ExceptionResponse,
)
from app.shared.database.session import get_db
from app.shared.middleware.auth import get_current_user_id
from app.shared.schemas.responses import created, ok

router = APIRouter(prefix="/doctors", tags=["Doctors -- Availability"])


@router.get(
    "/availability/summary",
    summary="Availability summary by specialty",
)
async def availability_summary(
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    from app.modules.dashboard.infrastructure.dashboard_query_service import (
        DashboardQueryService,
    )

    svc = DashboardQueryService(session)
    data = await svc.availability_summary()
    return ok(data=data, message="Availability summary retrieved successfully")


@router.get(
    "/{doctor_id}/availability",
    summary="Get availability blocks for a doctor",
)
async def get_availability(
    doctor_id: str,
    dow: Optional[int] = Query(None, ge=0, le=6, description="Day of week (0=Mon)"),
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    repo = SQLAlchemyAvailabilityRepository(session)
    items = await GetAvailability(repo).execute(doctor_id, day_of_week=dow)
    data = [AvailabilityResponse(**a.__dict__) for a in items]
    return ok(data=data, message="Disponibilidad obtenida exitosamente")


@router.post(
    "/{doctor_id}/availability",
    summary="Create availability block",
    status_code=201,
)
async def create_availability(
    doctor_id: str,
    body: AvailabilityCreate,
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    repo = SQLAlchemyAvailabilityRepository(session)
    dto = CreateAvailabilityDTO(
        fk_doctor_id=doctor_id,
        **body.model_dump(),
    )
    block = await CreateAvailability(repo).execute(dto, created_by=user_id)
    return created(
        data=AvailabilityResponse(**block.__dict__),
        message="Bloque de disponibilidad creado exitosamente",
    )


@router.patch(
    "/{doctor_id}/availability/{block_id}",
    summary="Update availability block",
    status_code=204,
)
async def update_availability(
    doctor_id: str,
    block_id: str,
    body: AvailabilityUpdate,
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    repo = SQLAlchemyAvailabilityRepository(session)
    dto = UpdateAvailabilityDTO(**body.model_dump(exclude_none=True))
    await UpdateAvailability(repo).execute(doctor_id, block_id, dto, updated_by=user_id)
    return Response(status_code=204)


@router.delete(
    "/{doctor_id}/availability/{block_id}",
    summary="Delete availability block (soft-delete)",
    status_code=204,
)
async def delete_availability(
    doctor_id: str,
    block_id: str,
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    repo = SQLAlchemyAvailabilityRepository(session)
    await DeleteAvailability(repo).execute(doctor_id, block_id, deleted_by=user_id)
    return Response(status_code=204)


@router.get(
    "/{doctor_id}/exceptions",
    summary="Check doctor exceptions",
)
async def get_exceptions(
    doctor_id: str,
    date: Optional[str] = Query(None, description="Filter by date (YYYY-MM-DD)"),
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    repo = SQLAlchemyExceptionRepository(session)
    items = await GetExceptions(repo).execute(doctor_id, exception_date=date)
    data = [ExceptionResponse(**e.__dict__) for e in items]
    return ok(data=data, message="Excepciones obtenidas exitosamente")
