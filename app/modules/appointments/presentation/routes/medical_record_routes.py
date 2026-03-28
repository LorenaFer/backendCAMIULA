from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.appointments.application.dtos.medical_record_dto import (
    UpsertMedicalRecordDTO,
)
from app.modules.appointments.application.use_cases.get_medical_record import (
    GetMedicalRecordUseCase,
)
from app.modules.appointments.application.use_cases.get_patient_medical_history import (
    GetPatientMedicalHistoryUseCase,
)
from app.modules.appointments.application.use_cases.mark_record_prepared import (
    MarkRecordPreparedUseCase,
)
from app.modules.appointments.application.use_cases.upsert_medical_record import (
    UpsertMedicalRecordUseCase,
)
from app.modules.appointments.infrastructure.repositories.sqlalchemy_medical_record_repository import (
    SQLAlchemyMedicalRecordRepository,
)
from app.modules.appointments.presentation.schemas.medical_record_schema import (
    MarkPreparedRequest,
    MedicalRecordResponse,
    PatientHistoryEntry,
    UpsertMedicalRecordRequest,
)
from app.shared.database.session import get_db
from app.shared.middleware.auth import require_permission
from app.shared.schemas.responses import ok

router = APIRouter(prefix="/medical-records", tags=["Medical Records"])


def _to_response(r) -> dict:
    return MedicalRecordResponse(
        id=r.id,
        cita_id=r.appointment_id,
        paciente_id=r.patient_id,
        doctor_id=r.doctor_id,
        schema_id=r.schema_id,
        schema_version=r.schema_version,
        evaluacion=r.evaluation,
        preparado=r.is_prepared,
        preparado_at=r.prepared_at,
        created_at=r.created_at,
        updated_at=r.updated_at,
    ).model_dump()


@router.get("")
async def get_medical_record(
    appointment_id: str = Query(...),
    _=Depends(require_permission("appointments:read")),
    db: AsyncSession = Depends(get_db),
):
    """Buscar historia médica por cita."""
    repo = SQLAlchemyMedicalRecordRepository(db)
    use_case = GetMedicalRecordUseCase(medical_record_repo=repo)
    record = await use_case.execute(appointment_id)
    if record is None:
        return ok(data=None, message="No se encontró historia médica")
    return ok(data=_to_response(record), message="Historia médica encontrada")


@router.put("")
async def upsert_medical_record(
    body: UpsertMedicalRecordRequest,
    user=Depends(require_permission("appointments:update")),
    db: AsyncSession = Depends(get_db),
):
    """Crear o actualizar historia médica (upsert por cita_id)."""
    repo = SQLAlchemyMedicalRecordRepository(db)
    use_case = UpsertMedicalRecordUseCase(medical_record_repo=repo)
    record = await use_case.execute(
        UpsertMedicalRecordDTO(
            appointment_id=body.cita_id,
            patient_id=body.paciente_id,
            doctor_id=body.doctor_id,
            schema_id=body.schema_id,
            schema_version=body.schema_version,
            evaluation=body.evaluacion,
        )
    )
    return ok(data=_to_response(record), message="Historia médica guardada")


@router.get("/patient/{patient_id}")
async def get_patient_history(
    patient_id: str,
    limit: int = Query(5, ge=1, le=50),
    exclude: Optional[str] = Query(None),
    _=Depends(require_permission("appointments:read")),
    db: AsyncSession = Depends(get_db),
):
    """Historial médico previo del paciente."""
    repo = SQLAlchemyMedicalRecordRepository(db)
    use_case = GetPatientMedicalHistoryUseCase(medical_record_repo=repo)
    records = await use_case.execute(
        patient_id=patient_id,
        limit=limit,
        exclude_appointment_id=exclude,
    )
    data = [
        PatientHistoryEntry(
            id=r.id,
            cita_id=r.appointment_id,
            doctor_id=r.doctor_id,
            schema_id=r.schema_id,
            evaluacion=r.evaluation,
            preparado=r.is_prepared,
            created_at=r.created_at,
        ).model_dump()
        for r in records
    ]
    return ok(data=data, message="Historial médico del paciente")


@router.patch("/{record_id}/prepared")
async def mark_prepared(
    record_id: str,
    body: MarkPreparedRequest,
    user=Depends(require_permission("appointments:update")),
    db: AsyncSession = Depends(get_db),
):
    """Marcar historia como preparada."""
    repo = SQLAlchemyMedicalRecordRepository(db)
    use_case = MarkRecordPreparedUseCase(medical_record_repo=repo)
    await use_case.execute(record_id, prepared_by=body.preparado_por)
    return ok(message="Historia marcada como preparada")
