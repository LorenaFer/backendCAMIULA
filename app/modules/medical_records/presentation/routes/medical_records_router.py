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
from app.modules.medical_records.domain.repositories.medical_record_repository import MedicalRecordRepository
from app.modules.medical_records.presentation.dependencies import get_medical_record_repo
from app.modules.medical_records.presentation.schemas.medical_record_schemas import (
    MarkPreparedBody,
    MedicalRecordResponse,
    MedicalRecordUpsert,
    PatientHistoryItem,
)
from app.shared.database.session import get_db
from app.shared.middleware.auth import get_current_user_id, get_optional_user_id
from app.shared.schemas.responses import created, ok

router = APIRouter(prefix="/medical-records", tags=["Medical Records"])


@router.get("/diagnostics/top", summary="Top diagnoses")
async def top_diagnostics(
    limit: int = Query(5, ge=1, le=50, description="Number of top diagnoses"),
    periodo: Optional[str] = Query(
        None, description="Period: week | month | year (from today)"
    ),
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_optional_user_id),
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
    user_id: str = Depends(get_optional_user_id),
):
    repo = get_medical_record_repo(session)
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
    user_id: str = Depends(get_optional_user_id),
):
    repo = get_medical_record_repo(session)
    history = await PatientHistory(repo).execute(patient_id, limit, exclude)
    data = [PatientHistoryItem(**item) for item in history]
    return ok(data=data, message="Patient history retrieved successfully")


@router.get("/{record_id}", summary="Find medical record by ID")
async def find_by_id(
    record_id: str,
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_optional_user_id),
):
    repo = get_medical_record_repo(session)
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
    repo = get_medical_record_repo(session)
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
    repo = get_medical_record_repo(session)
    record = await MarkPrepared(repo).execute(record_id, body.prepared_by)
    return ok(
        data=MedicalRecordResponse(**record.__dict__),
        message="Medical record marked as prepared",
    )


# ──────────────────────────────────────────────────────────────
# MEDICAL ORDERS (exam requests)
# ──────────────────────────────────────────────────────────────


@router.get("/orders/patient/{patient_id}", summary="Get exam orders for a patient")
async def get_patient_orders(
    patient_id: str,
    appointment_id: Optional[str] = Query(None, description="Filter by appointment"),
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_optional_user_id),
):
    from uuid import uuid4

    from sqlalchemy import select

    from app.modules.medical_records.infrastructure.models import MedicalOrderModel
    from app.shared.database.mixins import RecordStatus

    q = select(MedicalOrderModel).where(
        MedicalOrderModel.fk_patient_id == patient_id,
        MedicalOrderModel.status == RecordStatus.ACTIVE,
    )
    if appointment_id:
        q = q.where(MedicalOrderModel.fk_appointment_id == appointment_id)
    q = q.order_by(MedicalOrderModel.created_at.desc())

    result = await session.execute(q)
    orders = [
        {
            "id": o.id,
            "fk_appointment_id": o.fk_appointment_id,
            "fk_patient_id": o.fk_patient_id,
            "fk_doctor_id": o.fk_doctor_id,
            "order_type": o.order_type,
            "exam_name": o.exam_name,
            "notes": o.notes,
            "order_status": o.order_status,
            "created_at": o.created_at.isoformat() if o.created_at else None,
        }
        for o in result.scalars().all()
    ]
    return ok(data=orders, message="Medical orders retrieved")


@router.post("/orders", summary="Create exam order(s)", status_code=201)
async def create_orders(
    body: dict,
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_optional_user_id),
):
    """Create one or more exam orders for a consultation.

    Body: {
        fk_appointment_id: str,
        fk_patient_id: str,
        fk_doctor_id: str (optional, resolved from appointment),
        exams: [{exam_name: str, notes?: str}]
    }
    """
    from uuid import uuid4

    from sqlalchemy import select

    from app.modules.medical_records.infrastructure.models import MedicalOrderModel

    appointment_id = body.get("fk_appointment_id")
    patient_id = body.get("fk_patient_id")
    doctor_id = body.get("fk_doctor_id") or user_id
    exams = body.get("exams", [])

    if not appointment_id or not patient_id or not exams:
        from app.core.exceptions import AppException
        raise AppException("fk_appointment_id, fk_patient_id and exams are required", status_code=400)

    # Resolve doctor from appointment if not provided
    if doctor_id == user_id or doctor_id == "anonymous":
        from app.modules.appointments.infrastructure.models import AppointmentModel
        result = await session.execute(
            select(AppointmentModel.fk_doctor_id).where(AppointmentModel.id == appointment_id)
        )
        row = result.scalar_one_or_none()
        if row:
            doctor_id = row

    created_orders = []
    for exam in exams:
        order = MedicalOrderModel(
            id=str(uuid4()),
            fk_appointment_id=appointment_id,
            fk_patient_id=patient_id,
            fk_doctor_id=doctor_id,
            exam_name=exam.get("exam_name", exam) if isinstance(exam, dict) else str(exam),
            notes=exam.get("notes") if isinstance(exam, dict) else None,
            order_status="requested",
            created_by=user_id,
        )
        session.add(order)
        created_orders.append({
            "id": order.id,
            "exam_name": order.exam_name,
            "order_status": order.order_status,
        })

    await session.flush()
    return ok(data=created_orders, message=f"{len(created_orders)} exam order(s) created")
