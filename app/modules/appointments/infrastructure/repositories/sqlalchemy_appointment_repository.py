"""SQLAlchemy implementation of the appointment repository."""

from datetime import date as date_type
from datetime import datetime, time as time_type, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from sqlalchemy import Date, and_, cast, extract, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.modules.appointments.domain.entities.appointment import Appointment
from app.modules.appointments.domain.repositories.appointment_repository import (
    AppointmentRepository,
)
from app.modules.appointments.infrastructure.models import AppointmentModel
from app.modules.doctors.infrastructure.models import DoctorModel, SpecialtyModel
from app.modules.patients.infrastructure.models import PatientModel
from app.shared.database.mixins import RecordStatus


class SQLAlchemyAppointmentRepository(AppointmentRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _to_entity(
        model: AppointmentModel,
        patient_name: Optional[str] = None,
        patient_dni: Optional[str] = None,
        doctor_name: Optional[str] = None,
        specialty_name: Optional[str] = None,
        patient_university_relation: Optional[str] = None,
    ) -> Appointment:
        return Appointment(
            id=model.id,
            fk_patient_id=model.fk_patient_id,
            fk_doctor_id=model.fk_doctor_id,
            fk_specialty_id=model.fk_specialty_id,
            appointment_date=(
                model.appointment_date.isoformat()
                if model.appointment_date
                else None
            ),
            start_time=model.start_time.strftime("%H:%M") if isinstance(model.start_time, time_type) else model.start_time,
            end_time=model.end_time.strftime("%H:%M") if isinstance(model.end_time, time_type) else model.end_time,
            duration_minutes=model.duration_minutes,
            is_first_visit=model.is_first_visit,
            reason=model.reason,
            observations=model.observations,
            appointment_status=model.appointment_status,
            status=(
                model.status if isinstance(model.status, str) else model.status.value
            ),
            created_at=(
                model.created_at.isoformat() if model.created_at else None
            ),
            created_by=model.created_by,
            patient_name=patient_name,
            patient_dni=patient_dni,
            doctor_name=doctor_name,
            specialty_name=specialty_name,
            patient_university_relation=patient_university_relation,
        )

    def _base_active(self):
        return select(AppointmentModel).where(
            AppointmentModel.status == RecordStatus.ACTIVE
        )

    def _base_with_joins(self):
        """Select appointment + patient + doctor + specialty columns."""
        return (
            select(
                AppointmentModel,
                (PatientModel.first_name + " " + PatientModel.last_name).label(
                    "patient_name"
                ),
                PatientModel.dni.label("patient_dni"),
                (DoctorModel.first_name + " " + DoctorModel.last_name).label(
                    "doctor_name"
                ),
                SpecialtyModel.name.label("specialty_name"),
                PatientModel.university_relation.label(
                    "patient_university_relation"
                ),
            )
            .join(
                PatientModel,
                PatientModel.id == AppointmentModel.fk_patient_id,
            )
            .join(
                DoctorModel,
                DoctorModel.id == AppointmentModel.fk_doctor_id,
            )
            .join(
                SpecialtyModel,
                SpecialtyModel.id == AppointmentModel.fk_specialty_id,
            )
            .where(AppointmentModel.status == RecordStatus.ACTIVE)
        )

    def _row_to_entity(self, row) -> Appointment:
        model = row[0]
        return self._to_entity(
            model,
            patient_name=row.patient_name if hasattr(row, "patient_name") else None,
            patient_dni=row.patient_dni if hasattr(row, "patient_dni") else None,
            doctor_name=row.doctor_name if hasattr(row, "doctor_name") else None,
            specialty_name=row.specialty_name if hasattr(row, "specialty_name") else None,
            patient_university_relation=(
                row.patient_university_relation
                if hasattr(row, "patient_university_relation")
                else None
            ),
        )

    # ── Queries ──────────────────────────────────────────────

    async def find_by_id(self, appointment_id: str) -> Optional[Appointment]:
        stmt = self._base_with_joins().where(AppointmentModel.id == appointment_id)
        result = await self._session.execute(stmt)
        row = result.first()
        if not row:
            return None
        return self._row_to_entity(row)

    async def find_all(
        self,
        page: int,
        page_size: int,
        date_str: Optional[str] = None,
        doctor_id: Optional[str] = None,
        specialty_id: Optional[str] = None,
        status_filter: Optional[str] = None,
        q: Optional[str] = None,
        fk_patient_id: Optional[str] = None,
    ) -> Tuple[List[Appointment], int]:
        stmt = self._base_with_joins()

        if fk_patient_id:
            stmt = stmt.where(AppointmentModel.fk_patient_id == fk_patient_id)
        if date_str:
            stmt = stmt.where(
                AppointmentModel.appointment_date == date_type.fromisoformat(date_str)
            )
        if doctor_id:
            stmt = stmt.where(AppointmentModel.fk_doctor_id == doctor_id)
        if specialty_id:
            stmt = stmt.where(AppointmentModel.fk_specialty_id == specialty_id)
        if status_filter:
            stmt = stmt.where(AppointmentModel.appointment_status == status_filter)
        if q:
            pattern = f"%{q}%"
            stmt = stmt.where(
                or_(
                    PatientModel.first_name.ilike(pattern),
                    PatientModel.last_name.ilike(pattern),
                    PatientModel.dni.ilike(pattern),
                    (PatientModel.first_name + " " + PatientModel.last_name).ilike(pattern),
                )
            )

        # Count
        count_subq = stmt.subquery()
        count_q = select(func.count()).select_from(count_subq)
        total = (await self._session.execute(count_q)).scalar_one()

        # Paginate
        offset = (page - 1) * page_size
        stmt = stmt.order_by(
            AppointmentModel.appointment_date.desc(),
            AppointmentModel.start_time,
        ).offset(offset).limit(page_size)

        result = await self._session.execute(stmt)
        items = [self._row_to_entity(row) for row in result.all()]
        return items, total

    async def find_by_doctor_and_month(
        self,
        doctor_id: str,
        year: int,
        month: int,
        exclude_cancelled: bool = True,
    ) -> List[Appointment]:
        stmt = self._base_with_joins().where(
            AppointmentModel.fk_doctor_id == doctor_id,
            extract("year", AppointmentModel.appointment_date) == year,
            extract("month", AppointmentModel.appointment_date) == month,
        )
        if exclude_cancelled:
            stmt = stmt.where(AppointmentModel.appointment_status != "cancelada")
        stmt = stmt.order_by(
            AppointmentModel.appointment_date, AppointmentModel.start_time
        )
        result = await self._session.execute(stmt)
        return [self._row_to_entity(row) for row in result.all()]

    async def find_by_doctor_and_date(
        self,
        doctor_id: str,
        date_str: str,
        exclude_cancelled: bool = True,
    ) -> List[Appointment]:
        stmt = self._base_with_joins().where(
            AppointmentModel.fk_doctor_id == doctor_id,
            AppointmentModel.appointment_date == date_type.fromisoformat(date_str),
        )
        if exclude_cancelled:
            stmt = stmt.where(AppointmentModel.appointment_status != "cancelada")
        stmt = stmt.order_by(AppointmentModel.start_time)
        result = await self._session.execute(stmt)
        return [self._row_to_entity(row) for row in result.all()]

    async def check_double_booking(
        self, doctor_id: str, date_str: str, start_time: str
    ) -> bool:
        stmt = (
            select(func.count())
            .select_from(AppointmentModel)
            .where(
                AppointmentModel.fk_doctor_id == doctor_id,
                AppointmentModel.appointment_date == date_type.fromisoformat(date_str),
                AppointmentModel.start_time == self._parse_time(start_time),
                AppointmentModel.appointment_status != "cancelada",
                AppointmentModel.status == RecordStatus.ACTIVE,
            )
        )
        result = (await self._session.execute(stmt)).scalar_one()
        return result > 0

    async def update_status(
        self,
        appointment_id: str,
        new_status: str,
        updated_by: str,
    ) -> Appointment:
        stmt = self._base_active().where(AppointmentModel.id == appointment_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            raise NotFoundException("Cita no encontrada")

        model.appointment_status = new_status
        model.updated_by = updated_by
        model.updated_at = datetime.now(timezone.utc)
        await self._session.flush()
        await self._session.refresh(model)

        # Re-fetch with joins for full entity
        return await self.find_by_id(appointment_id)

    async def get_stats(
        self,
        date_str: Optional[str] = None,
        doctor_id: Optional[str] = None,
        specialty_id: Optional[str] = None,
        status_filter: Optional[str] = None,
    ) -> Dict[str, Any]:
        base = (
            select(AppointmentModel)
            .join(PatientModel, PatientModel.id == AppointmentModel.fk_patient_id)
            .join(DoctorModel, DoctorModel.id == AppointmentModel.fk_doctor_id)
            .join(SpecialtyModel, SpecialtyModel.id == AppointmentModel.fk_specialty_id)
            .where(AppointmentModel.status == RecordStatus.ACTIVE)
        )

        if date_str:
            base = base.where(
                AppointmentModel.appointment_date == date_type.fromisoformat(date_str)
            )
        if doctor_id:
            base = base.where(AppointmentModel.fk_doctor_id == doctor_id)
        if specialty_id:
            base = base.where(AppointmentModel.fk_specialty_id == specialty_id)
        if status_filter:
            base = base.where(AppointmentModel.appointment_status == status_filter)

        # Total count
        count_q = select(func.count()).select_from(base.subquery())
        total = (await self._session.execute(count_q)).scalar_one()

        # By status
        by_status_q = (
            select(
                AppointmentModel.appointment_status,
                func.count().label("cnt"),
            )
            .join(PatientModel, PatientModel.id == AppointmentModel.fk_patient_id)
            .join(DoctorModel, DoctorModel.id == AppointmentModel.fk_doctor_id)
            .join(SpecialtyModel, SpecialtyModel.id == AppointmentModel.fk_specialty_id)
            .where(AppointmentModel.status == RecordStatus.ACTIVE)
        )
        if date_str:
            by_status_q = by_status_q.where(
                AppointmentModel.appointment_date == date_type.fromisoformat(date_str)
            )
        if doctor_id:
            by_status_q = by_status_q.where(AppointmentModel.fk_doctor_id == doctor_id)
        if specialty_id:
            by_status_q = by_status_q.where(AppointmentModel.fk_specialty_id == specialty_id)
        if status_filter:
            by_status_q = by_status_q.where(AppointmentModel.appointment_status == status_filter)
        by_status_q = by_status_q.group_by(AppointmentModel.appointment_status)
        by_status_rows = (await self._session.execute(by_status_q)).all()
        by_status = {row[0]: row[1] for row in by_status_rows}

        # By specialty
        by_spec_q = (
            select(
                SpecialtyModel.name,
                func.count().label("cnt"),
            )
            .select_from(AppointmentModel)
            .join(PatientModel, PatientModel.id == AppointmentModel.fk_patient_id)
            .join(DoctorModel, DoctorModel.id == AppointmentModel.fk_doctor_id)
            .join(SpecialtyModel, SpecialtyModel.id == AppointmentModel.fk_specialty_id)
            .where(AppointmentModel.status == RecordStatus.ACTIVE)
        )
        if date_str:
            by_spec_q = by_spec_q.where(
                AppointmentModel.appointment_date == date_type.fromisoformat(date_str)
            )
        if doctor_id:
            by_spec_q = by_spec_q.where(AppointmentModel.fk_doctor_id == doctor_id)
        if specialty_id:
            by_spec_q = by_spec_q.where(AppointmentModel.fk_specialty_id == specialty_id)
        if status_filter:
            by_spec_q = by_spec_q.where(AppointmentModel.appointment_status == status_filter)
        by_spec_q = by_spec_q.group_by(SpecialtyModel.name)
        by_spec_rows = (await self._session.execute(by_spec_q)).all()
        by_specialty = [{"name": row[0], "count": row[1]} for row in by_spec_rows]

        # By doctor
        by_doc_q = (
            select(
                (DoctorModel.first_name + " " + DoctorModel.last_name).label("name"),
                SpecialtyModel.name.label("specialty"),
                func.count().label("cnt"),
                func.count()
                .filter(AppointmentModel.appointment_status == "atendida")
                .label("attended"),
            )
            .select_from(AppointmentModel)
            .join(PatientModel, PatientModel.id == AppointmentModel.fk_patient_id)
            .join(DoctorModel, DoctorModel.id == AppointmentModel.fk_doctor_id)
            .join(SpecialtyModel, SpecialtyModel.id == AppointmentModel.fk_specialty_id)
            .where(AppointmentModel.status == RecordStatus.ACTIVE)
        )
        if date_str:
            by_doc_q = by_doc_q.where(
                AppointmentModel.appointment_date == date_type.fromisoformat(date_str)
            )
        if doctor_id:
            by_doc_q = by_doc_q.where(AppointmentModel.fk_doctor_id == doctor_id)
        if specialty_id:
            by_doc_q = by_doc_q.where(AppointmentModel.fk_specialty_id == specialty_id)
        if status_filter:
            by_doc_q = by_doc_q.where(AppointmentModel.appointment_status == status_filter)
        by_doc_q = by_doc_q.group_by(
            DoctorModel.first_name,
            DoctorModel.last_name,
            SpecialtyModel.name,
        )
        by_doc_rows = (await self._session.execute(by_doc_q)).all()
        by_doctor = [
            {
                "name": row.name,
                "specialty": row.specialty,
                "count": row.cnt,
                "attended": row.attended,
            }
            for row in by_doc_rows
        ]

        # First time / returning
        first_q = (
            select(func.count())
            .select_from(AppointmentModel)
            .join(PatientModel, PatientModel.id == AppointmentModel.fk_patient_id)
            .join(DoctorModel, DoctorModel.id == AppointmentModel.fk_doctor_id)
            .join(SpecialtyModel, SpecialtyModel.id == AppointmentModel.fk_specialty_id)
            .where(
                AppointmentModel.status == RecordStatus.ACTIVE,
                AppointmentModel.is_first_visit.is_(True),
            )
        )
        if date_str:
            first_q = first_q.where(
                AppointmentModel.appointment_date == date_type.fromisoformat(date_str)
            )
        if doctor_id:
            first_q = first_q.where(AppointmentModel.fk_doctor_id == doctor_id)
        if specialty_id:
            first_q = first_q.where(AppointmentModel.fk_specialty_id == specialty_id)
        if status_filter:
            first_q = first_q.where(AppointmentModel.appointment_status == status_filter)
        first_time_count = (await self._session.execute(first_q)).scalar_one()
        returning_count = total - first_time_count

        # By patient type (university_relation)
        by_pt_q = (
            select(
                PatientModel.university_relation,
                func.count().label("cnt"),
            )
            .select_from(AppointmentModel)
            .join(PatientModel, PatientModel.id == AppointmentModel.fk_patient_id)
            .join(DoctorModel, DoctorModel.id == AppointmentModel.fk_doctor_id)
            .join(SpecialtyModel, SpecialtyModel.id == AppointmentModel.fk_specialty_id)
            .where(AppointmentModel.status == RecordStatus.ACTIVE)
        )
        if date_str:
            by_pt_q = by_pt_q.where(
                AppointmentModel.appointment_date == date_type.fromisoformat(date_str)
            )
        if doctor_id:
            by_pt_q = by_pt_q.where(AppointmentModel.fk_doctor_id == doctor_id)
        if specialty_id:
            by_pt_q = by_pt_q.where(AppointmentModel.fk_specialty_id == specialty_id)
        if status_filter:
            by_pt_q = by_pt_q.where(AppointmentModel.appointment_status == status_filter)
        by_pt_q = by_pt_q.group_by(PatientModel.university_relation)
        by_pt_rows = (await self._session.execute(by_pt_q)).all()
        by_patient_type = {row[0]: row[1] for row in by_pt_rows}

        # Daily trend (count per day-of-month)
        daily_q = (
            select(
                extract("day", AppointmentModel.appointment_date).label("d"),
                func.count().label("cnt"),
            )
            .select_from(AppointmentModel)
            .join(PatientModel, PatientModel.id == AppointmentModel.fk_patient_id)
            .join(DoctorModel, DoctorModel.id == AppointmentModel.fk_doctor_id)
            .join(SpecialtyModel, SpecialtyModel.id == AppointmentModel.fk_specialty_id)
            .where(AppointmentModel.status == RecordStatus.ACTIVE)
        )
        if date_str:
            daily_q = daily_q.where(
                AppointmentModel.appointment_date == date_type.fromisoformat(date_str)
            )
        if doctor_id:
            daily_q = daily_q.where(AppointmentModel.fk_doctor_id == doctor_id)
        if specialty_id:
            daily_q = daily_q.where(AppointmentModel.fk_specialty_id == specialty_id)
        if status_filter:
            daily_q = daily_q.where(AppointmentModel.appointment_status == status_filter)
        daily_q = daily_q.group_by("d").order_by("d")
        daily_rows = (await self._session.execute(daily_q)).all()
        # Build array indexed by day (sparse -> fill gaps with 0)
        daily_map = {int(row.d): row.cnt for row in daily_rows}
        max_day = max(daily_map.keys()) if daily_map else 0
        daily_trend = [daily_map.get(i, 0) for i in range(1, max_day + 1)]

        # Peak hours
        peak_q = (
            select(
                AppointmentModel.start_time.label("hour"),
                func.count().label("cnt"),
            )
            .select_from(AppointmentModel)
            .join(PatientModel, PatientModel.id == AppointmentModel.fk_patient_id)
            .join(DoctorModel, DoctorModel.id == AppointmentModel.fk_doctor_id)
            .join(SpecialtyModel, SpecialtyModel.id == AppointmentModel.fk_specialty_id)
            .where(AppointmentModel.status == RecordStatus.ACTIVE)
        )
        if date_str:
            peak_q = peak_q.where(
                AppointmentModel.appointment_date == date_type.fromisoformat(date_str)
            )
        if doctor_id:
            peak_q = peak_q.where(AppointmentModel.fk_doctor_id == doctor_id)
        if specialty_id:
            peak_q = peak_q.where(AppointmentModel.fk_specialty_id == specialty_id)
        if status_filter:
            peak_q = peak_q.where(AppointmentModel.appointment_status == status_filter)
        peak_q = peak_q.group_by(AppointmentModel.start_time).order_by(
            func.count().desc()
        )
        peak_rows = (await self._session.execute(peak_q)).all()
        peak_hours = [
            {
                "hour": row.hour.strftime("%H:%M") if isinstance(row.hour, time_type) else row.hour,
                "count": row.cnt,
            }
            for row in peak_rows
        ]

        return {
            "total": total,
            "by_status": by_status,
            "by_specialty": by_specialty,
            "by_doctor": by_doctor,
            "first_time_count": first_time_count,
            "returning_count": returning_count,
            "by_patient_type": by_patient_type,
            "daily_trend": daily_trend,
            "peak_hours": peak_hours,
        }

    async def find_non_cancelled_by_doctor_and_date(
        self, doctor_id: str, date_str: str
    ) -> List[Appointment]:
        stmt = (
            self._base_active()
            .where(
                AppointmentModel.fk_doctor_id == doctor_id,
                AppointmentModel.appointment_date == date_type.fromisoformat(date_str),
                AppointmentModel.appointment_status != "cancelada",
            )
            .order_by(AppointmentModel.start_time)
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(row) for row in result.scalars().all()]

    # ── Writes ───────────────────────────────────────────────

    @staticmethod
    def _parse_time(val):
        if isinstance(val, str):
            parts = val.split(":")
            return time_type(int(parts[0]), int(parts[1]))
        return val

    async def create(self, data: dict, created_by: str) -> Appointment:
        if isinstance(data.get("appointment_date"), str):
            data["appointment_date"] = date_type.fromisoformat(data["appointment_date"])
        if isinstance(data.get("start_time"), str):
            data["start_time"] = self._parse_time(data["start_time"])
        if isinstance(data.get("end_time"), str):
            data["end_time"] = self._parse_time(data["end_time"])

        model = AppointmentModel(
            id=str(uuid4()),
            created_by=created_by,
            **data,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)

        # Return with joins
        return await self.find_by_id(model.id)
