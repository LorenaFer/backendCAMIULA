from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.appointments.application.use_cases.create_specialty import (
    CreateSpecialtyUseCase,
)
from app.modules.appointments.application.use_cases.list_active_doctors import (
    ListActiveDoctorsUseCase,
)
from app.modules.appointments.application.use_cases.list_doctor_options import (
    ListDoctorOptionsUseCase,
)
from app.modules.appointments.application.use_cases.list_specialties import (
    ListSpecialtiesUseCase,
)
from app.modules.appointments.application.use_cases.toggle_specialty import (
    ToggleSpecialtyUseCase,
)
from app.modules.appointments.application.use_cases.update_specialty import (
    UpdateSpecialtyUseCase,
)
from app.modules.appointments.domain.entities.enums import DoctorStatus
from app.modules.appointments.infrastructure.repositories.sqlalchemy_doctor_repository import (
    SQLAlchemyDoctorRepository,
)
from app.modules.appointments.infrastructure.repositories.sqlalchemy_specialty_repository import (
    SQLAlchemySpecialtyRepository,
)
from app.modules.appointments.presentation.schemas.doctor_schema import (
    DoctorOptionResponse,
    DoctorResponse,
    SpecialtyCreateRequest,
    SpecialtyResponse,
    SpecialtyUpdateRequest,
)
from app.shared.database.session import get_db
from app.shared.middleware.auth import require_permission
from app.shared.schemas.responses import created, ok

router = APIRouter(tags=["Doctors"])


@router.get("/doctors")
async def list_doctors(
    active: Optional[bool] = Query(None),
    _=Depends(require_permission("doctors:read")),
    db: AsyncSession = Depends(get_db),
):
    """Listar doctores activos con su especialidad."""
    repo = SQLAlchemyDoctorRepository(db)
    use_case = ListActiveDoctorsUseCase(doctor_repo=repo)
    doctors = await use_case.execute()
    data = [
        DoctorResponse(
            id=d.id,
            nombre=d.first_name,
            apellido=d.last_name,
            especialidad_id=d.specialty_id,
            activo=d.doctor_status == DoctorStatus.ACTIVE.value,
            especialidad=SpecialtyResponse(
                id=d.specialty_id,
                nombre=d.specialty_name or "",
            ) if d.specialty_name else None,
        ).model_dump()
        for d in doctors
    ]
    return ok(data=data, message="Listado de doctores")


@router.get("/doctors/options")
async def list_doctor_options(
    _=Depends(require_permission("doctors:read")),
    db: AsyncSession = Depends(get_db),
):
    """Doctores para selectores (dropdowns). Incluye días de trabajo."""
    repo = SQLAlchemyDoctorRepository(db)
    use_case = ListDoctorOptionsUseCase(doctor_repo=repo)
    doctors = await use_case.execute()
    data = [
        DoctorOptionResponse(
            id=d.id,
            nombre_completo=d.display_name,
            especialidad=d.specialty_name or "",
            especialidad_id=d.specialty_id,
            dias_trabajo=d.work_days,
        ).model_dump()
        for d in doctors
    ]
    return ok(data=data, message="Opciones de doctores")


@router.get("/specialties")
async def list_specialties(
    _=Depends(require_permission("doctors:read")),
    db: AsyncSession = Depends(get_db),
):
    """Listar especialidades activas."""
    repo = SQLAlchemySpecialtyRepository(db)
    use_case = ListSpecialtiesUseCase(specialty_repo=repo)
    specialties = await use_case.execute()
    data = [
        SpecialtyResponse(id=s.id, nombre=s.name, activo=s.is_active).model_dump()
        for s in specialties
    ]
    return ok(data=data, message="Listado de especialidades")


@router.post("/specialties", status_code=201)
async def create_specialty(
    body: SpecialtyCreateRequest,
    user=Depends(require_permission("doctors:write")),
    db: AsyncSession = Depends(get_db),
):
    """Crear nueva especialidad."""
    repo = SQLAlchemySpecialtyRepository(db)
    use_case = CreateSpecialtyUseCase(specialty_repo=repo)
    specialty = await use_case.execute(body.nombre, created_by=user.id)
    return created(
        data=SpecialtyResponse(
            id=specialty.id, nombre=specialty.name, activo=specialty.is_active
        ).model_dump(),
        message="Especialidad creada",
    )


@router.put("/specialties/{specialty_id}")
async def update_specialty(
    specialty_id: str,
    body: SpecialtyUpdateRequest,
    user=Depends(require_permission("doctors:write")),
    db: AsyncSession = Depends(get_db),
):
    """Actualizar nombre de especialidad."""
    repo = SQLAlchemySpecialtyRepository(db)
    use_case = UpdateSpecialtyUseCase(specialty_repo=repo)
    specialty = await use_case.execute(specialty_id, body.nombre, updated_by=user.id)
    return ok(
        data=SpecialtyResponse(
            id=specialty.id, nombre=specialty.name, activo=specialty.is_active
        ).model_dump(),
        message="Especialidad actualizada",
    )


@router.patch("/specialties/{specialty_id}/toggle")
async def toggle_specialty(
    specialty_id: str,
    user=Depends(require_permission("doctors:write")),
    db: AsyncSession = Depends(get_db),
):
    """Alternar estado activo/inactivo de una especialidad."""
    repo = SQLAlchemySpecialtyRepository(db)
    use_case = ToggleSpecialtyUseCase(specialty_repo=repo)
    specialty = await use_case.execute(specialty_id, updated_by=user.id)
    return ok(
        data=SpecialtyResponse(
            id=specialty.id, nombre=specialty.name, activo=specialty.is_active
        ).model_dump(),
        message="Estado de especialidad actualizado",
    )
