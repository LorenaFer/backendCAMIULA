"""FastAPI routes for Doctor resource."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.doctors.application.use_cases.doctors.get_doctor_options import (
    GetDoctorOptions,
)
from app.modules.doctors.application.use_cases.doctors.get_doctors import (
    GetDoctors,
)
from app.modules.doctors.domain.repositories.doctor_repository import DoctorRepository
from app.modules.doctors.presentation.dependencies import get_doctor_repo
from app.modules.doctors.presentation.schemas.doctor_schemas import (
    DoctorOptionResponse,
    DoctorResponse,
)
from app.shared.database.session import get_db
from app.shared.middleware.auth import get_optional_user_id
from app.shared.schemas.responses import ok

router = APIRouter(prefix="/doctors", tags=["Doctors -- Doctors"])


@router.get("/options", summary="Lightweight doctor list for selects")
async def get_doctor_options(
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_optional_user_id),
):
    """Lightweight doctor list optimized for dropdown selects. Returns id, name, specialty, and computed working days."""
    repo = get_doctor_repo(session)
    items = await GetDoctorOptions(repo).execute()
    data = [DoctorOptionResponse(**d.__dict__) for d in items]
    return ok(data=data, message="Doctor options retrieved")


@router.get("", summary="List active doctors with specialty")
async def list_doctors(
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_optional_user_id),
):
    """List all active doctors with their embedded specialty information."""
    repo = get_doctor_repo(session)
    items = await GetDoctors(repo).execute()
    data = [DoctorResponse(**d.__dict__) for d in items]
    return ok(data=data, message="Doctors retrieved successfully")
