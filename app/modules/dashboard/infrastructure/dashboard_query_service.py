"""Aggregation query service for the Dashboard BI module.

This service performs read-only queries across all domain modules to produce
KPIs, charts, and trend data.  It owns NO tables — every query targets
models from patients, appointments, doctors, medical_records, and inventory.
"""

from datetime import date, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import Date as SADate, case, cast, distinct, extract, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.modules.appointments.infrastructure.models import AppointmentModel
from app.modules.doctors.infrastructure.models import (
    DoctorAvailabilityModel,
    DoctorModel,
    SpecialtyModel,
)
from app.modules.inventory.infrastructure.models import (
    BatchModel,
    DispatchItemModel,
    DispatchModel,
    MedicationModel,
)
from app.modules.medical_records.infrastructure.models import MedicalRecordModel
from app.modules.patients.infrastructure.models import PatientModel
from app.shared.database.mixins import RecordStatus


# Pure functions re-exported from domain layer for backward compatibility
from app.modules.dashboard.domain.date_utils import (  # noqa: F401
    parse_date as _parse_date,
    period_range as _period_range,
)


_ACTIVE = RecordStatus.ACTIVE.value


class DashboardQueryService:
    """Stateless service — instantiate with an ``AsyncSession``."""

    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    # ------------------------------------------------------------------
    # 1. KPIs
    # ------------------------------------------------------------------

    async def kpis(
        self, fecha: date, start: date, end: date
    ) -> Dict[str, Any]:
        # -- Appointment counts ----------------------------------------
        base = select(AppointmentModel).where(
            AppointmentModel.status == _ACTIVE,
            AppointmentModel.appointment_date.between(start, end),
        )

        total_q = select(func.count()).select_from(base.subquery())
        total_appointments = (await self._s.execute(total_q)).scalar() or 0

        today_q = (
            select(func.count())
            .select_from(AppointmentModel)
            .where(
                AppointmentModel.status == _ACTIVE,
                AppointmentModel.appointment_date == fecha,
            )
        )
        appointments_today = (await self._s.execute(today_q)).scalar() or 0

        pending_q = select(func.count()).select_from(
            base.where(AppointmentModel.appointment_status == "pendiente").subquery()
        )
        pending_appointments = (await self._s.execute(pending_q)).scalar() or 0

        # -- Rates -----------------------------------------------------
        attended_q = select(func.count()).select_from(
            base.where(AppointmentModel.appointment_status == "atendida").subquery()
        )
        attended = (await self._s.execute(attended_q)).scalar() or 0

        no_show_q = select(func.count()).select_from(
            base.where(AppointmentModel.appointment_status == "no_asistio").subquery()
        )
        no_shows = (await self._s.execute(no_show_q)).scalar() or 0

        cancelled_q = select(func.count()).select_from(
            base.where(AppointmentModel.appointment_status == "cancelada").subquery()
        )
        cancelled = (await self._s.execute(cancelled_q)).scalar() or 0

        denom = total_appointments or 1
        attendance_rate = round(attended / denom * 100, 1)
        no_show_rate = round(no_shows / denom * 100, 1)
        cancellation_rate = round(cancelled / denom * 100, 1)

        # -- Patient counts --------------------------------------------
        total_patients_q = (
            select(func.count())
            .select_from(PatientModel)
            .where(PatientModel.status == _ACTIVE)
        )
        total_patients = (await self._s.execute(total_patients_q)).scalar() or 0

        new_patients_q = (
            select(func.count())
            .select_from(PatientModel)
            .where(
                PatientModel.status == _ACTIVE,
                PatientModel.is_new.is_(True),
            )
        )
        new_patients = (await self._s.execute(new_patients_q)).scalar() or 0

        # -- Doctor count ----------------------------------------------
        total_doctors_q = (
            select(func.count())
            .select_from(DoctorModel)
            .where(DoctorModel.status == _ACTIVE)
        )
        total_doctors = (await self._s.execute(total_doctors_q)).scalar() or 0

        # -- Inventory value -------------------------------------------
        inv_q = (
            select(func.coalesce(func.sum(BatchModel.quantity_available * BatchModel.unit_cost), 0))
            .where(
                BatchModel.status == _ACTIVE,
                BatchModel.batch_status == "available",
            )
        )
        inventory_value = float((await self._s.execute(inv_q)).scalar() or 0)

        return {
            "total_appointments": total_appointments,
            "appointments_today": appointments_today,
            "pending_appointments": pending_appointments,
            "attendance_rate": attendance_rate,
            "no_show_rate": no_show_rate,
            "cancellation_rate": cancellation_rate,
            "total_patients": total_patients,
            "new_patients": new_patients,
            "total_doctors": total_doctors,
            "inventory_value": round(inventory_value, 2),
        }

    # ------------------------------------------------------------------
    # 2. Appointments by status
    # ------------------------------------------------------------------

    async def appointments_by_status(
        self, start: date, end: date
    ) -> Dict[str, int]:
        q = (
            select(
                AppointmentModel.appointment_status,
                func.count().label("cnt"),
            )
            .where(
                AppointmentModel.status == _ACTIVE,
                AppointmentModel.appointment_date.between(start, end),
            )
            .group_by(AppointmentModel.appointment_status)
        )
        rows = (await self._s.execute(q)).all()
        return {row[0]: row[1] for row in rows}

    # ------------------------------------------------------------------
    # 3. Appointments by specialty
    # ------------------------------------------------------------------

    async def appointments_by_specialty(
        self, start: date, end: date
    ) -> List[Dict[str, Any]]:
        q = (
            select(
                SpecialtyModel.name,
                func.count().label("count"),
            )
            .select_from(AppointmentModel)
            .join(
                SpecialtyModel,
                SpecialtyModel.id == AppointmentModel.fk_specialty_id,
            )
            .where(
                AppointmentModel.status == _ACTIVE,
                AppointmentModel.appointment_date.between(start, end),
            )
            .group_by(SpecialtyModel.name)
            .order_by(func.count().desc())
        )
        rows = (await self._s.execute(q)).all()
        return [{"name": row[0], "count": row[1]} for row in rows]

    # ------------------------------------------------------------------
    # 4. Daily trend (last 7 days from fecha)
    # ------------------------------------------------------------------

    async def daily_trend(self, fecha: date) -> List[int]:
        days = [fecha - timedelta(days=i) for i in range(6, -1, -1)]
        q = (
            select(
                AppointmentModel.appointment_date,
                func.count().label("cnt"),
            )
            .where(
                AppointmentModel.status == _ACTIVE,
                AppointmentModel.appointment_date.between(days[0], days[-1]),
            )
            .group_by(AppointmentModel.appointment_date)
        )
        rows = (await self._s.execute(q)).all()
        by_date = {row[0]: row[1] for row in rows}
        return [by_date.get(d, 0) for d in days]

    # ------------------------------------------------------------------
    # 5. Hourly distribution
    # ------------------------------------------------------------------

    async def hourly_distribution(
        self, start: date, end: date
    ) -> List[Dict[str, Any]]:
        q = (
            select(
                extract("hour", AppointmentModel.start_time).label("h"),
                func.count().label("cnt"),
            )
            .where(
                AppointmentModel.status == _ACTIVE,
                AppointmentModel.appointment_date.between(start, end),
            )
            .group_by("h")
            .order_by("h")
        )
        rows = (await self._s.execute(q)).all()
        return [
            {"hour": f"{int(row[0]):02d}:00", "count": row[1]}
            for row in rows
        ]

    # ------------------------------------------------------------------
    # 6. Heatmap (day_of_week x hour) — 5 rows (Mon-Fri), 12 cols (7-18h)
    # ------------------------------------------------------------------

    async def heatmap(
        self, fecha_desde: date, fecha_hasta: date
    ) -> List[List[int]]:
        q = (
            select(
                extract("isodow", AppointmentModel.appointment_date).label("dow"),
                extract("hour", AppointmentModel.start_time).label("h"),
                func.count().label("cnt"),
            )
            .where(
                AppointmentModel.status == _ACTIVE,
                AppointmentModel.appointment_date.between(fecha_desde, fecha_hasta),
            )
            .group_by("dow", "h")
        )
        rows = (await self._s.execute(q)).all()

        matrix: List[List[int]] = [[0] * 12 for _ in range(5)]
        for row in rows:
            dow = int(row[0])  # 1=Mon .. 5=Fri
            hour = int(row[1])
            if 1 <= dow <= 5 and 7 <= hour <= 18:
                matrix[dow - 1][hour - 7] = row[2]
        return matrix

    # ------------------------------------------------------------------
    # 7. Occupancy by specialty
    # ------------------------------------------------------------------

    async def occupancy_by_specialty(
        self, start: date, end: date
    ) -> List[Dict[str, Any]]:
        # Available slots: count availability blocks per specialty
        avail_q = (
            select(
                SpecialtyModel.name,
                func.count(DoctorAvailabilityModel.id).label("available_slots"),
            )
            .select_from(DoctorAvailabilityModel)
            .join(DoctorModel, DoctorModel.id == DoctorAvailabilityModel.fk_doctor_id)
            .join(SpecialtyModel, SpecialtyModel.id == DoctorModel.fk_specialty_id)
            .where(
                DoctorAvailabilityModel.status == _ACTIVE,
                DoctorModel.status == _ACTIVE,
            )
            .group_by(SpecialtyModel.name)
        )
        avail_rows = (await self._s.execute(avail_q)).all()
        avail_map = {row[0]: row[1] for row in avail_rows}

        # Booked appointments per specialty in range
        booked_q = (
            select(
                SpecialtyModel.name,
                func.count().label("booked"),
            )
            .select_from(AppointmentModel)
            .join(SpecialtyModel, SpecialtyModel.id == AppointmentModel.fk_specialty_id)
            .where(
                AppointmentModel.status == _ACTIVE,
                AppointmentModel.appointment_date.between(start, end),
            )
            .group_by(SpecialtyModel.name)
        )
        booked_rows = (await self._s.execute(booked_q)).all()
        booked_map = {row[0]: row[1] for row in booked_rows}

        names = sorted(set(list(avail_map.keys()) + list(booked_map.keys())))
        return [
            {
                "name": n,
                "available_slots": avail_map.get(n, 0),
                "booked": booked_map.get(n, 0),
            }
            for n in names
        ]

    # ------------------------------------------------------------------
    # 8. Absenteeism by specialty
    # ------------------------------------------------------------------

    async def absenteeism_by_specialty(
        self, start: date, end: date
    ) -> List[Dict[str, Any]]:
        q = (
            select(
                SpecialtyModel.name,
                func.count().label("total"),
                func.sum(
                    case(
                        (AppointmentModel.appointment_status == "no_asistio", 1),
                        else_=0,
                    )
                ).label("no_shows"),
            )
            .select_from(AppointmentModel)
            .join(SpecialtyModel, SpecialtyModel.id == AppointmentModel.fk_specialty_id)
            .where(
                AppointmentModel.status == _ACTIVE,
                AppointmentModel.appointment_date.between(start, end),
            )
            .group_by(SpecialtyModel.name)
        )
        rows = (await self._s.execute(q)).all()
        result = []
        for row in rows:
            total = row[1] or 0
            no_shows = row[2] or 0
            rate = round(no_shows / total * 100, 1) if total else 0.0
            result.append({
                "name": row[0],
                "total": total,
                "no_shows": no_shows,
                "rate": rate,
            })
        return result

    # ------------------------------------------------------------------
    # 9. Performance by doctor
    # ------------------------------------------------------------------

    async def performance_by_doctor(
        self, start: date, end: date
    ) -> List[Dict[str, Any]]:
        q = (
            select(
                (DoctorModel.first_name + " " + DoctorModel.last_name).label("name"),
                SpecialtyModel.name.label("specialty"),
                func.count().label("count"),
                func.sum(
                    case(
                        (AppointmentModel.appointment_status == "atendida", 1),
                        else_=0,
                    )
                ).label("attended"),
            )
            .select_from(AppointmentModel)
            .join(DoctorModel, DoctorModel.id == AppointmentModel.fk_doctor_id)
            .join(SpecialtyModel, SpecialtyModel.id == DoctorModel.fk_specialty_id)
            .where(
                AppointmentModel.status == _ACTIVE,
                AppointmentModel.appointment_date.between(start, end),
            )
            .group_by(DoctorModel.first_name, DoctorModel.last_name, SpecialtyModel.name)
            .order_by(func.count().desc())
        )
        rows = (await self._s.execute(q)).all()
        return [
            {
                "name": row[0],
                "specialty": row[1],
                "count": row[2],
                "attended": row[3] or 0,
            }
            for row in rows
        ]

    # ------------------------------------------------------------------
    # 10. Patients by type (university_relation)
    # ------------------------------------------------------------------

    async def patients_by_type(self) -> Dict[str, int]:
        q = (
            select(
                PatientModel.university_relation,
                func.count().label("cnt"),
            )
            .where(PatientModel.status == _ACTIVE)
            .group_by(PatientModel.university_relation)
        )
        rows = (await self._s.execute(q)).all()
        return {row[0]: row[1] for row in rows}

    # ------------------------------------------------------------------
    # 11. Patients by sex
    # ------------------------------------------------------------------

    async def patients_by_sex(self) -> Dict[str, int]:
        q = (
            select(
                func.coalesce(PatientModel.sex, "N/D").label("sex"),
                func.count().label("cnt"),
            )
            .where(PatientModel.status == _ACTIVE)
            .group_by("sex")
        )
        rows = (await self._s.execute(q)).all()
        return {row[0]: row[1] for row in rows}

    # ------------------------------------------------------------------
    # 12. First-time vs returning counts
    # ------------------------------------------------------------------

    async def visit_counts(self) -> Tuple[int, int]:
        first_q = (
            select(func.count())
            .select_from(PatientModel)
            .where(PatientModel.status == _ACTIVE, PatientModel.is_new.is_(True))
        )
        first_time = (await self._s.execute(first_q)).scalar() or 0

        returning_q = (
            select(func.count())
            .select_from(PatientModel)
            .where(PatientModel.status == _ACTIVE, PatientModel.is_new.is_(False))
        )
        returning = (await self._s.execute(returning_q)).scalar() or 0
        return first_time, returning

    # ------------------------------------------------------------------
    # 13. Top diagnoses
    # ------------------------------------------------------------------

    async def top_diagnoses(
        self, limit: int = 5, start: Optional[date] = None, end: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """Top diagnoses extracted from medical_records.evaluation->diagnosis."""
        q = select(MedicalRecordModel.evaluation).where(
            MedicalRecordModel.status == _ACTIVE,
            MedicalRecordModel.evaluation.isnot(None),
        )
        if start and end:
            # Join appointments to filter by date
            q = (
                q.join(
                    AppointmentModel,
                    AppointmentModel.id == MedicalRecordModel.fk_appointment_id,
                )
                .where(AppointmentModel.appointment_date.between(start, end))
            )

        rows = (await self._s.execute(q)).all()

        counts: Dict[Tuple[str, str], int] = {}
        for (evaluation,) in rows:
            if not isinstance(evaluation, dict):
                continue
            diagnosis = evaluation.get("diagnosis", {})
            if not isinstance(diagnosis, dict):
                continue
            code = diagnosis.get("code", "")
            desc = diagnosis.get("description", "")
            if not code and not desc:
                continue
            key = (code or "N/A", desc or "N/A")
            counts[key] = counts.get(key, 0) + 1

        sorted_items = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:limit]
        return [
            {"code": k[0], "description": k[1], "count": v}
            for k, v in sorted_items
        ]

    # ------------------------------------------------------------------
    # 14. Inventory summary
    # ------------------------------------------------------------------

    async def inventory_summary(self) -> Dict[str, Any]:
        today = date.today()

        total_meds_q = (
            select(func.count())
            .select_from(MedicationModel)
            .where(MedicationModel.status == _ACTIVE)
        )
        total_medications = (await self._s.execute(total_meds_q)).scalar() or 0

        # Critical stock: medications with total available < 10
        critical_sub = (
            select(BatchModel.fk_medication_id)
            .where(
                BatchModel.status == _ACTIVE,
                BatchModel.batch_status == "available",
            )
            .group_by(BatchModel.fk_medication_id)
            .having(func.sum(BatchModel.quantity_available) < 10)
        )
        critical_q = select(func.count()).select_from(critical_sub.subquery())
        critical_stock = (await self._s.execute(critical_q)).scalar() or 0

        # Expiring within 30 days
        expiring_q = (
            select(func.count())
            .select_from(BatchModel)
            .where(
                BatchModel.status == _ACTIVE,
                BatchModel.batch_status == "available",
                BatchModel.expiration_date <= today + timedelta(days=30),
                BatchModel.expiration_date >= today,
            )
        )
        expiring_batches = (await self._s.execute(expiring_q)).scalar() or 0

        # Estimated value
        val_q = (
            select(
                func.coalesce(
                    func.sum(BatchModel.quantity_available * BatchModel.unit_cost), 0
                )
            )
            .where(
                BatchModel.status == _ACTIVE,
                BatchModel.batch_status == "available",
            )
        )
        estimated_value = float((await self._s.execute(val_q)).scalar() or 0)

        return {
            "total_medications": total_medications,
            "critical_stock": critical_stock,
            "expiring_batches": expiring_batches,
            "estimated_value": round(estimated_value, 2),
        }

    # ------------------------------------------------------------------
    # 15. Top consumption (dispatched medications)
    # ------------------------------------------------------------------

    async def top_consumption(
        self, start: date, end: date, limit: int = 5
    ) -> List[Dict[str, Any]]:
        q = (
            select(
                DispatchItemModel.fk_medication_id.label("medication_id"),
                MedicationModel.generic_name,
                func.sum(DispatchItemModel.quantity_dispatched).label("total_dispatched"),
                func.count(distinct(DispatchModel.fk_patient_id)).label("patient_count"),
            )
            .select_from(DispatchItemModel)
            .join(DispatchModel, DispatchModel.id == DispatchItemModel.fk_dispatch_id)
            .join(MedicationModel, MedicationModel.id == DispatchItemModel.fk_medication_id)
            .where(
                DispatchItemModel.status == _ACTIVE,
                DispatchModel.status == _ACTIVE,
                cast(DispatchModel.dispatch_date, SADate).between(start, end),
            )
            .group_by(DispatchItemModel.fk_medication_id, MedicationModel.generic_name)
            .order_by(func.sum(DispatchItemModel.quantity_dispatched).desc())
            .limit(limit)
        )
        rows = (await self._s.execute(q)).all()
        return [
            {
                "medication_id": row[0],
                "generic_name": row[1],
                "total_dispatched": int(row[2] or 0),
                "patient_count": int(row[3] or 0),
            }
            for row in rows
        ]

    # ------------------------------------------------------------------
    # 16. Patient demographics (for standalone endpoint)
    # ------------------------------------------------------------------

    async def patient_demographics(self) -> Dict[str, Any]:
        by_type = await self.patients_by_type()
        by_sex = await self.patients_by_sex()
        first_time, returning = await self.visit_counts()
        return {
            "patients_by_type": by_type,
            "patients_by_sex": by_sex,
            "first_time_count": first_time,
            "returning_count": returning,
        }

    # ------------------------------------------------------------------
    # 17. Doctors availability summary
    # ------------------------------------------------------------------

    async def availability_summary(self) -> List[Dict[str, Any]]:
        q = (
            select(
                SpecialtyModel.name,
                func.count(distinct(DoctorModel.id)).label("total_doctors"),
                func.count(DoctorAvailabilityModel.id).label("total_blocks"),
            )
            .select_from(DoctorModel)
            .join(SpecialtyModel, SpecialtyModel.id == DoctorModel.fk_specialty_id)
            .outerjoin(
                DoctorAvailabilityModel,
                DoctorAvailabilityModel.fk_doctor_id == DoctorModel.id,
            )
            .where(
                DoctorModel.status == _ACTIVE,
                DoctorModel.doctor_status == "active",
            )
            .group_by(SpecialtyModel.name)
            .order_by(SpecialtyModel.name)
        )
        rows = (await self._s.execute(q)).all()
        return [
            {
                "specialty": row[0],
                "total_doctors": row[1],
                "total_blocks": row[2],
            }
            for row in rows
        ]
