"""FastAPI routes for Specialty resource."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.doctors.application.dtos.specialty_dto import (
    CreateSpecialtyDTO,
    UpdateSpecialtyDTO,
)
from app.modules.doctors.application.use_cases.specialties.create_specialty import (
    CreateSpecialty,
)
from app.modules.doctors.application.use_cases.specialties.get_specialties import (
    GetSpecialties,
)
from app.modules.doctors.application.use_cases.specialties.toggle_specialty import (
    ToggleSpecialty,
)
from app.modules.doctors.application.use_cases.specialties.update_specialty import (
    UpdateSpecialty,
)
from app.modules.doctors.domain.repositories.specialty_repository import SpecialtyRepository
from app.modules.doctors.presentation.dependencies import get_specialty_repo
from app.modules.doctors.presentation.schemas.specialty_schemas import (
    SpecialtyCreate,
    SpecialtyResponse,
    SpecialtyUpdate,
)
from app.shared.database.session import get_db
from app.shared.middleware.auth import get_current_user_id, get_optional_user_id
from app.shared.schemas.responses import created, ok

router = APIRouter(prefix="/specialties", tags=["Doctors -- Specialties"])


@router.get("", summary="List all specialties")
async def list_specialties(
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_optional_user_id),
):
    repo = get_specialty_repo(session)
    items = await GetSpecialties(repo).execute()
    data = [SpecialtyResponse(**s.__dict__) for s in items]
    return ok(data=data, message="Especialidades obtenidas exitosamente")


@router.post("", summary="Create specialty", status_code=201)
async def create_specialty(
    body: SpecialtyCreate,
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    repo = get_specialty_repo(session)
    dto = CreateSpecialtyDTO(**body.model_dump())
    specialty = await CreateSpecialty(repo).execute(dto, created_by=user_id)
    return created(
        data=SpecialtyResponse(**specialty.__dict__),
        message="Especialidad creada exitosamente",
    )


@router.put("/{id}", summary="Update specialty")
async def update_specialty(
    id: str,
    body: SpecialtyUpdate,
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    repo = get_specialty_repo(session)
    dto = UpdateSpecialtyDTO(**body.model_dump(exclude_none=True))
    specialty = await UpdateSpecialty(repo).execute(id, dto, updated_by=user_id)
    return ok(
        data=SpecialtyResponse(**specialty.__dict__),
        message="Especialidad actualizada exitosamente",
    )


@router.patch("/{id}/toggle", summary="Toggle specialty active/inactive")
async def toggle_specialty(
    id: str,
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    repo = get_specialty_repo(session)
    specialty = await ToggleSpecialty(repo).execute(id, updated_by=user_id)
    return ok(
        data=SpecialtyResponse(**specialty.__dict__),
        message="Estado de especialidad actualizado exitosamente",
    )
