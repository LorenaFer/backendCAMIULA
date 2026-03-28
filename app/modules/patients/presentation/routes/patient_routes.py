from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.patients.application.dtos.patient_dto import CreatePatientDTO
from app.modules.patients.application.use_cases.create_patient import (
    CreatePatientUseCase,
)
from app.modules.patients.application.use_cases.get_max_nhm import GetMaxNhmUseCase
from app.modules.patients.application.use_cases.get_patient_profile import (
    GetPatientProfileUseCase,
)
from app.modules.patients.application.use_cases.search_patient import (
    SearchPatientByCedulaUseCase,
    SearchPatientByNhmUseCase,
)
from app.modules.patients.domain.entities.patient import Patient
from app.modules.patients.infrastructure.repositories.sqlalchemy_patient_repository import (
    SQLAlchemyPatientRepository,
)
from app.modules.patients.presentation.schemas.patient_schema import (
    MaxNhmResponse,
    PatientCreateRequest,
    PatientCreatedResponse,
    PatientFullResponse,
    PatientPublicResponse,
)
from app.shared.database.session import get_db
from app.shared.middleware.auth import require_permission
from app.shared.schemas.common import StandardResponse
from app.shared.schemas.responses import created, ok

router = APIRouter(prefix="/patients", tags=["Patients"])


def _to_public(p: Patient) -> dict:
    return PatientPublicResponse(
        id=p.id,
        nhm=p.nhm,
        nombre=p.first_name,
        apellido=p.last_name,
        relacion_univ=p.university_relation,
        es_nuevo=p.is_new,
    ).model_dump()


def _to_full(p: Patient) -> dict:
    return PatientFullResponse(
        id=p.id,
        nhm=p.nhm,
        cedula=p.cedula,
        nombre=p.first_name,
        apellido=p.last_name,
        sexo=p.sex,
        fecha_nacimiento=p.birth_date,
        lugar_nacimiento=p.birth_place,
        edad=p.age,
        estado_civil=p.marital_status,
        religion=p.religion,
        procedencia=p.origin,
        direccion_habitacion=p.home_address,
        telefono=p.phone,
        profesion=p.profession,
        ocupacion_actual=p.current_occupation,
        direccion_trabajo=p.work_address,
        clasificacion_economica=p.economic_classification,
        relacion_univ=p.university_relation,
        parentesco=p.family_relationship,
        titular_nhm=p.holder_patient_id,
        datos_medicos=p.medical_data,
        contacto_emergencia=p.emergency_contact,
        es_nuevo=p.is_new,
        created_at=p.created_at,
    ).model_dump()


def _to_created(p: Patient) -> dict:
    return PatientCreatedResponse(
        id=p.id,
        nhm=p.nhm,
        cedula=p.cedula,
        nombre=p.first_name,
        apellido=p.last_name,
        relacion_univ=p.university_relation,
        es_nuevo=p.is_new,
        created_at=p.created_at,
    ).model_dump()


@router.get("", response_model=StandardResponse[PatientPublicResponse])
async def search_patient(
    nhm: Optional[int] = Query(None),
    cedula: Optional[str] = Query(None),
    _=Depends(require_permission("patients:read")),
    db: AsyncSession = Depends(get_db),
):
    """Buscar paciente por NHM o cédula. Retorna datos reducidos."""
    repo = SQLAlchemyPatientRepository(db)

    if nhm is not None:
        use_case = SearchPatientByNhmUseCase(patient_repo=repo)
        patient = await use_case.execute(nhm)
    elif cedula is not None:
        use_case_ced = SearchPatientByCedulaUseCase(patient_repo=repo)
        patient = await use_case_ced.execute(cedula)
    else:
        from app.core.exceptions import AppException
        raise AppException("Debe especificar nhm o cedula", status_code=422)

    if patient is None:
        return ok(data=None, message="Paciente no encontrado")

    return ok(data=_to_public(patient), message="Paciente encontrado")


@router.get("/full", response_model=StandardResponse[PatientFullResponse])
async def get_patient_full(
    cedula: str = Query(...),
    _=Depends(require_permission("patients:read")),
    db: AsyncSession = Depends(get_db),
):
    """Ficha completa del paciente por cédula."""
    repo = SQLAlchemyPatientRepository(db)
    use_case = GetPatientProfileUseCase(patient_repo=repo)
    patient = await use_case.execute(cedula)
    return ok(data=_to_full(patient), message="Ficha completa del paciente")


@router.get("/max-nhm", response_model=StandardResponse[MaxNhmResponse])
async def get_max_nhm(
    _=Depends(require_permission("patients:read")),
    db: AsyncSession = Depends(get_db),
):
    """Obtener el último NHM asignado."""
    repo = SQLAlchemyPatientRepository(db)
    use_case = GetMaxNhmUseCase(patient_repo=repo)
    max_nhm = await use_case.execute()
    return ok(
        data=MaxNhmResponse(max_nhm=max_nhm).model_dump(),
        message="Último NHM asignado",
    )


@router.post("", status_code=201, response_model=StandardResponse[PatientCreatedResponse])
async def create_patient(
    body: PatientCreateRequest,
    user=Depends(require_permission("patients:create")),
    db: AsyncSession = Depends(get_db),
):
    """Registrar un nuevo paciente."""
    repo = SQLAlchemyPatientRepository(db)
    use_case = CreatePatientUseCase(patient_repo=repo)

    dto = CreatePatientDTO(
        cedula=body.cedula,
        first_name=body.first_name,
        last_name=body.last_name,
        university_relation=body.university_relation,
        sex=body.sex,
        birth_date=body.birth_date,
        birth_place=body.birth_place,
        marital_status=body.marital_status,
        religion=body.religion,
        origin=body.origin,
        home_address=body.home_address,
        phone=body.phone,
        profession=body.profession,
        current_occupation=body.current_occupation,
        work_address=body.work_address,
        economic_classification=body.economic_classification,
        family_relationship=body.family_relationship,
        holder_patient_id=body.holder_patient_id,
        medical_data=body.medical_data.model_dump() if body.medical_data else None,
        emergency_contact=body.emergency_contact.model_dump() if body.emergency_contact else None,
    )

    patient = await use_case.execute(dto, created_by=user.id)
    return created(data=_to_created(patient), message="Paciente registrado exitosamente")
