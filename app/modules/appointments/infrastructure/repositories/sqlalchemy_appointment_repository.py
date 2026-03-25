from __future__ import annotations

from datetime import date, time
from typing import List, Optional, Tuple
from uuid import uuid4

from sqlalchemy import extract, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.appointments.domain.entities.appointment import (
    Appointment,
    AppointmentJoinData,
)
from app.modules.appointments.domain.entities.enums import AppointmentStatus
from app.modules.appointments.domain.repositories.appointment_repository import (
    AppointmentRepository,
)
from app.modules.appointments.infrastructure.models import (
    AppointmentModel,
    DoctorModel,
    SpecialtyModel,
)
from app.modules.patients.infrastructure.models import PatientModel
from app.shared.database.mixins import RecordStatus


class SQLAlchemyAppointmentRepository(AppointmentRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _to_entity(model: AppointmentModel) -> Appointment:
        return Appointment(
            id=model.id,
            patient_id=model.fk_patient_id,
            doctor_id=model.fk_doctor_id,
            specialty_id=model.fk_specialty_id,
            appointment_date=model.appointment_date,
            start_time=model.start_time,
            end_time=model.end_time,
            duration_minutes=model.duration_minutes,
            is_first_visit=model.is_first_visit,
            reason=model.reason,
            observations=model.observations,
            appointment_status=model.appointment_status,
            created_by=model.created_by,
            created_at=str(model.created_at) if model.created_at else None,
        )

    @classmethod
    def _to_entity_with_joins(
        cls,
        apt: AppointmentModel,
        patient: PatientModel,
        doctor: DoctorModel,
        specialty_name: str,
    ) -> Appointment:
        entity = cls._to_entity(apt)
        entity.join_data = AppointmentJoinData(
            patient_id=patient.id,
            patient_nhm=patient.nhm,
            patient_first_name=patient.first_name,
            patient_last_name=patient.last_name,
            patient_cedula=patient.cedula,
            patient_university_relation=patient.university_relation,
            doctor_id=doctor.id,
            doctor_first_name=doctor.first_name,
            doctor_last_name=doctor.last_name,
            specialty_name=specialty_name,
        )
        return entity

    async def create(self, appointment: Appointment) -> Appointment:
        model = AppointmentModel(
            id=appointment.id or str(uuid4()),
            fk_patient_id=appointment.patient_id,
            fk_doctor_id=appointment.doctor_id,
            fk_specialty_id=appointment.specialty_id,
            appointment_date=appointment.appointment_date,
            start_time=appointment.start_time,
            end_time=appointment.end_time,
            duration_minutes=appointment.duration_minutes,
            is_first_visit=appointment.is_first_visit,
            reason=appointment.reason,
            observations=appointment.observations,
            appointment_status=appointment.appointment_status,
            created_by=appointment.created_by,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_entity(model)

    async def get_by_id(self, appointment_id: str) -> Optional[Appointment]:
        stmt = select(AppointmentModel).where(
            AppointmentModel.id == appointment_id,
            AppointmentModel.status == RecordStatus.ACTIVE,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_detail(self, appointment_id: str) -> Optional[Appointment]:
        """Cita con datos de paciente y doctor via JOIN. O(log n)."""
        stmt = (
            select(AppointmentModel, PatientModel, DoctorModel, SpecialtyModel.name)
            .join(PatientModel, AppointmentModel.fk_patient_id == PatientModel.id)
            .join(DoctorModel, AppointmentModel.fk_doctor_id == DoctorModel.id)
            .join(
                SpecialtyModel, AppointmentModel.fk_specialty_id == SpecialtyModel.id
            )
            .where(
                AppointmentModel.id == appointment_id,
                AppointmentModel.status == RecordStatus.ACTIVE,
            )
        )
        result = await self._session.execute(stmt)
        row = result.one_or_none()
        if row is None:
            return None
        return self._to_entity_with_joins(row[0], row[1], row[2], row[3])

    async def list_filtered(
        self,
        page: int,
        page_size: int,
        fecha: Optional[date] = None,
        doctor_id: Optional[str] = None,
        specialty_id: Optional[str] = None,
        estado: Optional[str] = None,
        q: Optional[str] = None,
        mes: Optional[str] = None,
        excluir_canceladas: bool = False,
    ) -> Tuple[List[Appointment], int]:
        """Lista citas con filtros y paginación. O(log n + k).

        Selecciona solo columnas necesarias de Patient y Doctor para evitar
        cargar JSONB blobs (medical_data, emergency_contact) en listados.
        """
        base = (
            select(
                AppointmentModel,
                PatientModel.id.label("p_id"),
                PatientModel.nhm,
                PatientModel.first_name.label("p_first_name"),
                PatientModel.last_name.label("p_last_name"),
                PatientModel.cedula,
                PatientModel.university_relation,
                DoctorModel.id.label("d_id"),
                DoctorModel.first_name.label("d_first_name"),
                DoctorModel.last_name.label("d_last_name"),
                SpecialtyModel.name.label("specialty_name"),
            )
            .join(PatientModel, AppointmentModel.fk_patient_id == PatientModel.id)
            .join(DoctorModel, AppointmentModel.fk_doctor_id == DoctorModel.id)
            .join(
                SpecialtyModel, AppointmentModel.fk_specialty_id == SpecialtyModel.id
            )
            .where(AppointmentModel.status == RecordStatus.ACTIVE)
        )

        count_base = (
            select(func.count())
            .select_from(AppointmentModel)
            .where(AppointmentModel.status == RecordStatus.ACTIVE)
        )

        if fecha:
            base = base.where(AppointmentModel.appointment_date == fecha)
            count_base = count_base.where(AppointmentModel.appointment_date == fecha)
        if doctor_id:
            base = base.where(AppointmentModel.fk_doctor_id == doctor_id)
            count_base = count_base.where(AppointmentModel.fk_doctor_id == doctor_id)
        if specialty_id:
            base = base.where(AppointmentModel.fk_specialty_id == specialty_id)
            count_base = count_base.where(
                AppointmentModel.fk_specialty_id == specialty_id
            )
        if estado:
            base = base.where(
                AppointmentModel.appointment_status == estado.upper()
            )
            count_base = count_base.where(
                AppointmentModel.appointment_status == estado.upper()
            )
        if mes:
            # mes formato YYYY-MM
            parts = mes.split("-")
            if len(parts) == 2:
                year, month = int(parts[0]), int(parts[1])
                base = base.where(
                    extract("year", AppointmentModel.appointment_date) == year,
                    extract("month", AppointmentModel.appointment_date) == month,
                )
                count_base = count_base.where(
                    extract("year", AppointmentModel.appointment_date) == year,
                    extract("month", AppointmentModel.appointment_date) == month,
                )
        if excluir_canceladas:
            excluded = {s.value for s in AppointmentStatus.excluded()}
            base = base.where(
                AppointmentModel.appointment_status.notin_(excluded)
            )
            count_base = count_base.where(
                AppointmentModel.appointment_status.notin_(excluded)
            )
        if q:
            search = f"%{q}%"
            q_filter = or_(
                PatientModel.first_name.ilike(search),
                PatientModel.last_name.ilike(search),
                PatientModel.cedula.ilike(search),
            )
            base = base.where(q_filter)
            # Solo agregar JOIN con patients al count cuando hay búsqueda de texto
            count_base = (
                count_base
                .join(PatientModel, AppointmentModel.fk_patient_id == PatientModel.id)
                .where(q_filter)
            )

        # Count
        total = (await self._session.execute(count_base)).scalar_one()

        # Paginate
        stmt = (
            base.order_by(
                AppointmentModel.appointment_date.desc(),
                AppointmentModel.start_time.asc(),
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self._session.execute(stmt)

        items = []
        for row in result.all():
            entity = self._to_entity(row[0])
            entity.join_data = AppointmentJoinData(
                patient_id=row.p_id,
                patient_nhm=row.nhm,
                patient_first_name=row.p_first_name,
                patient_last_name=row.p_last_name,
                patient_cedula=row.cedula,
                patient_university_relation=row.university_relation,
                doctor_id=row.d_id,
                doctor_first_name=row.d_first_name,
                doctor_last_name=row.d_last_name,
                specialty_name=row.specialty_name,
            )
            items.append(entity)
        return items, total

    async def update_status(
        self, appointment_id: str, new_status: str, updated_by: str
    ) -> None:
        stmt = select(AppointmentModel).where(
            AppointmentModel.id == appointment_id
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            model.appointment_status = new_status
            model.updated_by = updated_by
            await self._session.flush()

    async def is_slot_occupied(
        self,
        doctor_id: str,
        appointment_date: date,
        start_time: time,
        end_time: time,
        exclude_id: Optional[str] = None,
    ) -> bool:
        """O(log n) con índice compuesto (appointment_date, fk_doctor_id)."""
        active_statuses = {s.value for s in AppointmentStatus.schedulable()}
        stmt = (
            select(func.count())
            .select_from(AppointmentModel)
            .where(
                AppointmentModel.fk_doctor_id == doctor_id,
                AppointmentModel.appointment_date == appointment_date,
                AppointmentModel.start_time < end_time,
                AppointmentModel.end_time > start_time,
                AppointmentModel.appointment_status.in_(active_statuses),
                AppointmentModel.status == RecordStatus.ACTIVE,
            )
        )
        if exclude_id:
            stmt = stmt.where(AppointmentModel.id != exclude_id)
        result = await self._session.execute(stmt)
        return result.scalar_one() > 0
