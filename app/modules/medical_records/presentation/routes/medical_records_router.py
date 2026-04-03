"""FastAPI routes for Medical Records."""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.modules.medical_records.application.dtos.medical_record_dto import (
    UpsertMedicalRecordDTO,
)
from app.modules.medical_records.application.use_cases.find_by_appointment import (
    FindByAppointment,
)
from app.modules.medical_records.application.use_cases.find_by_id import FindById
from app.modules.medical_records.application.use_cases.mark_prepared import MarkPrepared
from app.modules.medical_records.application.use_cases.patient_history import (
    PatientHistory,
)
from app.modules.medical_records.application.use_cases.upsert_record import UpsertRecord
from app.modules.medical_records.infrastructure.repositories.sqlalchemy_medical_record_repository import (
    SQLAlchemyMedicalRecordRepository,
)
from app.modules.medical_records.presentation.schemas.medical_record_schemas import (
    MarkPreparedBody,
    MedicalRecordResponse,
    MedicalRecordUpsert,
    PatientHistoryItem,
)
from app.shared.database.session import get_db
from app.shared.middleware.auth import get_current_user_id
from app.shared.schemas.responses import created, ok

router = APIRouter(prefix="/medical-records", tags=["Medical Records"])


@router.get("/diagnostics/top", summary="Top diagnoses")
async def top_diagnostics(
    limit: int = Query(5, ge=1, le=50, description="Number of top diagnoses"),
    periodo: Optional[str] = Query(
        None, description="Period: week | month | year (from today)"
    ),
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    from datetime import date as _date

    from app.modules.dashboard.infrastructure.dashboard_query_service import (
        DashboardQueryService,
        _parse_date,
        _period_range,
    )

    svc = DashboardQueryService(session)
    start = None
    end = None
    if periodo:
        ref = _date.today()
        start, end = _period_range(ref, periodo)

    data = await svc.top_diagnoses(limit=limit, start=start, end=end)
    return ok(data=data, message="Top diagnoses retrieved successfully")


@router.get("", summary="Find medical record by appointment ID")
async def find_by_appointment(
    appointment_id: str = Query(..., description="Appointment UUID"),
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    repo = SQLAlchemyMedicalRecordRepository(session)
    record = await FindByAppointment(repo).execute(appointment_id)
    if not record:
        raise NotFoundException("Medical record not found for this appointment.")
    return ok(
        data=MedicalRecordResponse(**record.__dict__),
        message="Medical record retrieved successfully",
    )


@router.get("/patient/{patient_id}", summary="Patient history summary")
async def patient_history(
    patient_id: str,
    limit: int = Query(5, ge=1, le=50),
    exclude: Optional[str] = Query(None, description="Record ID to exclude"),
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    repo = SQLAlchemyMedicalRecordRepository(session)
    history = await PatientHistory(repo).execute(patient_id, limit, exclude)
    data = [PatientHistoryItem(**item) for item in history]
    return ok(data=data, message="Patient history retrieved successfully")


@router.get("/{record_id}", summary="Find medical record by ID")
async def find_by_id(
    record_id: str,
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    repo = SQLAlchemyMedicalRecordRepository(session)
    record = await FindById(repo).execute(record_id)
    if not record:
        raise NotFoundException("Medical record not found.")
    return ok(
        data=MedicalRecordResponse(**record.__dict__),
        message="Medical record retrieved successfully",
    )


@router.put("", summary="Upsert medical record")
async def upsert_record(
    body: MedicalRecordUpsert,
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    repo = SQLAlchemyMedicalRecordRepository(session)
    dto = UpsertMedicalRecordDTO(**body.model_dump())
    record, was_created = await UpsertRecord(repo).execute(dto, user_id)
    response = MedicalRecordResponse(**record.__dict__)
    if was_created:
        return created(data=response, message="Medical record created successfully")
    return ok(data=response, message="Medical record updated successfully")


@router.patch("/{record_id}/prepared", summary="Mark medical record as prepared")
async def mark_prepared(
    record_id: str,
    body: MarkPreparedBody,
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    repo = SQLAlchemyMedicalRecordRepository(session)
    record = await MarkPrepared(repo).execute(record_id, body.prepared_by)
    return ok(
        data=MedicalRecordResponse(**record.__dict__),
        message="Medical record marked as prepared",
    )
