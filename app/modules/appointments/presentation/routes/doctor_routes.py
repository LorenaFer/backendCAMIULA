from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.appointments.application.use_cases.list_active_doctors import (
    ListActiveDoctorsUseCase,
)
from app.modules.appointments.application.use_cases.list_doctor_options import (
    ListDoctorOptionsUseCase,
)
from app.modules.appointments.application.use_cases.list_specialties import (
    ListSpecialtiesUseCase,
)
from app.modules.appointments.infrastructure.repositories.sqlalchemy_doctor_repository import (
    SQLAlchemyDoctorRepository,
)
from app.modules.appointments.infrastructure.repositories.sqlalchemy_specialty_repository import (
    SQLAlchemySpecialtyRepository,
)
from app.modules.appointments.presentation.schemas.doctor_schema import (
    DoctorOptionResponse,
    DoctorResponse,
    SpecialtyResponse,
)
from app.shared.database.session import get_db
from app.shared.middleware.auth import require_permission
from app.shared.schemas.responses import ok

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
            activo=d.doctor_status == "ACTIVE",
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
        SpecialtyResponse(id=s.id, nombre=s.name).model_dump()
        for s in specialties
    ]
    return ok(data=data, message="Listado de especialidades")
