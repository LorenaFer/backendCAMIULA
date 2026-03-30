"""Rutas FastAPI del módulo de pacientes."""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.patients.application.dtos.patient_dto import (
    CreatePatientDTO,
    GetPatientHistoryDTO,
    SearchPatientDTO,
)
from app.modules.patients.application.use_cases.create_patient import CreatePatient
from app.modules.patients.application.use_cases.get_patient_history import (
    GetPatientHistory,
)
from app.modules.patients.application.use_cases.search_patient import SearchPatient
from app.modules.patients.infrastructure.repositories.sqlalchemy_patient_repository import (
    SQLAlchemyPatientRepository,
)
from app.modules.patients.presentation.schemas.patient_schema import (
    PatientCreateRequest,
    PatientHistoryResponse,
    PatientResponse,
)
from app.shared.database.session import get_db
from app.shared.middleware.auth import get_current_user_id
from app.shared.schemas.responses import created, ok

router = APIRouter(prefix="/patients", tags=["Patients"])


@router.get("/search", summary="Buscar paciente por cédula o NHM")
async def search_patient(
    cedula: Optional[str] = Query(None),
    nhm: Optional[int] = Query(None, ge=1),
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    repo = SQLAlchemyPatientRepository(session)
    patient = await SearchPatient(repo).execute(SearchPatientDTO(cedula=cedula, nhm=nhm))
    return ok(
        data=PatientResponse(**patient.__dict__).model_dump(mode="json"),
        message="Paciente encontrado",
    )


@router.post("", status_code=201, summary="Crear paciente")
async def create_patient(
    body: PatientCreateRequest,
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    repo = SQLAlchemyPatientRepository(session)
    payload = body.model_dump(exclude_none=True)
    payload["datos_medicos"] = (
        body.datos_medicos.model_dump(exclude_none=True)
        if body.datos_medicos
        else {}
    )
    payload["contacto_emergencia"] = (
        body.contacto_emergencia.model_dump(exclude_none=True)
        if body.contacto_emergencia
        else {}
    )

    patient = await CreatePatient(repo).execute(
        dto=CreatePatientDTO(**payload),
        created_by=user_id,
    )
    return created(
        data=PatientResponse(**patient.__dict__).model_dump(mode="json"),
        message="Paciente creado",
    )


@router.get("/{id}/history", summary="Historial médico resumido")
async def get_patient_history(
    id: str,
    limit: int = Query(5, ge=1, le=50),
    exclude_appointment_id: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    repo = SQLAlchemyPatientRepository(session)
    items = await GetPatientHistory(repo).execute(
        GetPatientHistoryDTO(
            patient_id=id,
            limit=limit,
            exclude_appointment_id=exclude_appointment_id,
        )
    )
    return ok(
        data=[PatientHistoryResponse(**item.__dict__).model_dump() for item in items],
        message="Historial obtenido",
    )
