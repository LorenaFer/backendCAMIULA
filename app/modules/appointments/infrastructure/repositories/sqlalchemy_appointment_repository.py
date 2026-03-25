from __future__ import annotations

from datetime import date, time
from typing import List, Optional, Tuple
from uuid import uuid4

from sqlalchemy import extract, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.appointments.domain.entities.appointment import Appointment
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

    @staticmethod
    def _to_entity_with_joins(
        apt: AppointmentModel,
        patient: PatientModel,
        doctor: DoctorModel,
        specialty_name: str,
    ) -> Appointment:
        entity = Appointment(
            id=apt.id,
            patient_id=apt.fk_patient_id,
            doctor_id=apt.fk_doctor_id,
            specialty_id=apt.fk_specialty_id,
            appointment_date=apt.appointment_date,
            start_time=apt.start_time,
            end_time=apt.end_time,
            duration_minutes=apt.duration_minutes,
            is_first_visit=apt.is_first_visit,
            reason=apt.reason,
            observations=apt.observations,
            appointment_status=apt.appointment_status,
            created_by=apt.created_by,
            created_at=str(apt.created_at) if apt.created_at else None,
        )
        entity.patient_data = {
            "id": patient.id,
            "nhm": patient.nhm,
            "nombre": patient.first_name,
            "apellido": patient.last_name,
            "cedula": patient.cedula,
            "relacion_univ": patient.university_relation,
        }
        entity.doctor_data = {
            "id": doctor.id,
            "nombre": doctor.first_name,
            "apellido": doctor.last_name,
            "especialidad": specialty_name,
        }
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
        """Lista citas con filtros y paginación. O(log n + k)."""
        base = (
            select(AppointmentModel, PatientModel, DoctorModel, SpecialtyModel.name)
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
            .join(PatientModel, AppointmentModel.fk_patient_id == PatientModel.id)
            .where(AppointmentModel.status == RecordStatus.ACTIVE)
        )

        # Aplicar filtros
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
            excluded = {"CANCELLED", "NO_SHOW"}
            base = base.where(
                AppointmentModel.appointment_status.notin_(excluded)
            )
            count_base = count_base.where(
                AppointmentModel.appointment_status.notin_(excluded)
            )
        if q:
            search = f"%{q}%"
            base = base.where(
                or_(
                    PatientModel.first_name.ilike(search),
                    PatientModel.last_name.ilike(search),
                    PatientModel.cedula.ilike(search),
                )
            )
            count_base = count_base.where(
                or_(
                    PatientModel.first_name.ilike(search),
                    PatientModel.last_name.ilike(search),
                    PatientModel.cedula.ilike(search),
                )
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

        items = [
            self._to_entity_with_joins(row[0], row[1], row[2], row[3])
            for row in result.all()
        ]
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
        active_statuses = {"PENDING", "CONFIRMED"}
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
