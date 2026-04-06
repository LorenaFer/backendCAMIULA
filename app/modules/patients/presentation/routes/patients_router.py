"""FastAPI routes for the Patient resource."""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.patients.application.dtos.patient_dto import (
    CreatePatientDTO,
    RegisterPatientDTO,
)
from app.modules.patients.application.use_cases.create_patient import CreatePatient
from app.modules.patients.application.use_cases.get_max_nhm import GetMaxNhm
from app.modules.patients.application.use_cases.list_patients import ListPatients
from app.modules.patients.application.use_cases.register_patient import (
    RegisterPatient,
)
from app.modules.patients.application.use_cases.search_patient import (
    SearchPatientByCedula,
    SearchPatientByNhm,
)
from app.modules.patients.domain.repositories.patient_repository import (
    PatientRepository,
)
from app.modules.patients.presentation.dependencies import get_patient_repo
from app.modules.patients.presentation.schemas.patient_schemas import (
    MaxNhmResponse,
    PatientCreate,
    PatientPublicResponse,
    PatientRegister,
    PatientResponse,
)
from app.shared.database.session import get_db
from app.shared.middleware.auth import get_current_user_id, get_optional_user_id
from app.shared.schemas.responses import created, ok, paginated

router = APIRouter(prefix="/patients", tags=["Patients"])


# ── Static routes first (before any {id} params) ─────────────


@router.get("/demographics", summary="Patient demographics breakdown")
async def patient_demographics(
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Returns patient distribution statistics: count by university relation type (estudiante, personal, docente, familia, externo), count by sex, and first-time vs returning patient counts. Used by the dashboard."""
    from app.modules.dashboard.infrastructure.dashboard_query_service import (
        DashboardQueryService,
    )

    svc = DashboardQueryService(session)
    data = await svc.patient_demographics()
    return ok(data=data, message="Patient demographics retrieved successfully")


@router.get("/full", summary="Get full patient by id, cedula or NHM")
async def get_patient_full(
    id: Optional[str] = Query(None, description="Patient UUID"),
    cedula: Optional[str] = Query(None, description="Patient cedula"),
    nhm: Optional[int] = Query(None, description="Patient NHM"),
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_optional_user_id),
):
    """Retrieve complete patient data including medical_data (JSONB) and emergency_contact. Accepts one of three identifiers: `id` (UUID), `cedula`, or `nhm`. Returns null if not found."""
    repo = get_patient_repo(session)
    patient = None
    if id:
        patient = await repo.find_by_id(id)
    elif cedula:
        patient = await SearchPatientByCedula(repo).execute(cedula)
    elif nhm is not None:
        patient = await SearchPatientByNhm(repo).execute(nhm)

    return ok(
        data=PatientResponse(**patient.__dict__) if patient else None,
        message="Paciente obtenido exitosamente" if patient else "Paciente no encontrado",
    )


@router.get("/max-nhm", summary="Get highest NHM registered")
async def get_max_nhm(
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Returns the highest NHM (Hospital Medical Number) currently registered. Used by the registration form to display the next available NHM."""
    repo = get_patient_repo(session)
    max_nhm = await GetMaxNhm(repo).execute()
    return ok(
        data=MaxNhmResponse(max_nhm=max_nhm),
        message="Maximo NHM obtenido exitosamente",
    )


@router.get("", summary="List patients or search by NHM/cedula/text")
async def list_or_search_patients(
    nhm: Optional[int] = Query(None, description="Search by NHM"),
    cedula: Optional[str] = Query(None, description="Search by cedula"),
    search: Optional[str] = Query(None, description="Search by cedula, name or NHM"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=10000),
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_optional_user_id),
):
    """Search and list patients with multiple strategies. Priority: nhm (exact) > cedula (exact) > search (text) > list all. Text search queries cedula, first_name, last_name, and NHM. Paginated, sorted by last_name."""
    repo = get_patient_repo(session)

    # Search by NHM -> returns PatientPublic | null
    if nhm is not None:
        patient = await SearchPatientByNhm(repo).execute(nhm)
        return ok(
            data=PatientPublicResponse(**patient.__dict__) if patient else None,
            message="Paciente encontrado" if patient else "Paciente no encontrado",
        )

    # Search by cedula -> returns PatientPublic | null
    if cedula:
        patient = await SearchPatientByCedula(repo).execute(cedula)
        return ok(
            data=PatientPublicResponse(**patient.__dict__) if patient else None,
            message="Paciente encontrado" if patient else "Paciente no encontrado",
        )

    # Paginated list with optional text search
    items, total = await repo.find_all(page, page_size, search=search)
    data = [PatientResponse(**p.__dict__) for p in items]
    return paginated(data, total, page, page_size, "Pacientes obtenidos exitosamente")


@router.get("/{patient_id}", summary="Get patient by ID")
async def get_patient_by_id(
    patient_id: str,
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_optional_user_id),
):
    """Retrieve a patient by their UUID. Returns 404 if not found."""
    repo = get_patient_repo(session)
    patient = await repo.find_by_id(patient_id)
    if not patient:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("Paciente no encontrado")
    return ok(
        data=PatientResponse(**patient.__dict__),
        message="Paciente obtenido exitosamente",
    )


@router.post("", summary="Create patient", status_code=201)
async def create_patient(
    body: PatientCreate,
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Register a new patient with auto-generated NHM. NHM assignment uses pg_advisory_xact_lock for concurrency safety. The cedula must be unique."""
    repo = get_patient_repo(session)
    dto = CreatePatientDTO(**body.model_dump())
    patient = await CreatePatient(repo).execute(dto, created_by=user_id)
    return created(
        data=PatientResponse(**patient.__dict__),
        message="Paciente creado exitosamente",
    )


@router.post("/register", summary="Register patient (ULA portal)", status_code=201)
async def register_patient(
    body: PatientRegister,
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_optional_user_id),
):
    """Self-registration endpoint for the ULA patient portal. No authentication required. Accepts extended fields (country, state, city, blood_type, emergency contact) that the backend composes into JSONB fields. Returns minimal data for security."""
    repo = get_patient_repo(session)
    dto = RegisterPatientDTO(**body.model_dump())
    patient = await RegisterPatient(repo).execute(dto, created_by=user_id)
    return created(
        data=PatientPublicResponse(**patient.__dict__),
        message="Paciente registrado exitosamente",
    )
