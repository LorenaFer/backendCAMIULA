"""Query service for epidemiological reports.

Shared data fetching and helper functions for EPI-12, EPI-13, EPI-15.
"""

from __future__ import annotations

import calendar
from datetime import date, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, select as sa_select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.appointments.infrastructure.models import AppointmentModel
from app.modules.doctors.infrastructure.models import DoctorModel
from app.modules.medical_records.infrastructure.models import MedicalRecordModel
from app.modules.patients.infrastructure.models import PatientModel
from app.shared.database.mixins import RecordStatus
from app.modules.reports.domain.epi_catalogue import AGE_GROUP_KEYS, AGE_GROUP_BOUNDS



# Pure functions re-exported from domain layer
from app.modules.reports.domain.epi_functions import (  # noqa: F401
    calculate_age,
    epi_week_date_range,
    get_age_group,
    matches_cie10_range,
    month_date_range,
)



def _extract_cie10(evaluation: Optional[dict]) -> Optional[str]:
    """Safely extract CIE-10 code from the evaluation JSONB.

    Expected path: evaluation -> diagnostico -> cie10
    Complexity: O(1).
    """
    if not evaluation:
        return None
    diagnostico = evaluation.get("diagnostico")
    if not diagnostico:
        return None
    if isinstance(diagnostico, dict):
        return diagnostico.get("cie10")
    return None


def _extract_disease_name(evaluation: Optional[dict]) -> Optional[str]:
    """Safely extract disease description from the evaluation JSONB.

    Expected path: evaluation -> diagnostico -> descripcion
    Complexity: O(1).
    """
    if not evaluation:
        return None
    diagnostico = evaluation.get("diagnostico")
    if not diagnostico:
        return None
    if isinstance(diagnostico, dict):
        return diagnostico.get("descripcion")
    return None




async def _fetch_records_in_range(
    db: AsyncSession,
    start_date: date,
    end_date: date,
) -> list:
    """Fetch joined appointment + medical_record + patient rows in a date range.

    Returns list of tuples:
        (appointment_date, evaluation, birth_date, sex, first_name, last_name,
         home_address, doctor_first_name, doctor_last_name)

    Query plan relies on B-tree index on appointments.appointment_date for
    range scan -> O(log N + k) where k = matching rows.
    """
    from sqlalchemy import and_, select as sa_select

    stmt = (
        sa_select(
            AppointmentModel.appointment_date,
            MedicalRecordModel.evaluation,
            PatientModel.birth_date,
            PatientModel.sex,
            PatientModel.first_name,
            PatientModel.last_name,
            PatientModel.home_address,
            DoctorModel.first_name.label("doctor_first_name"),
            DoctorModel.last_name.label("doctor_last_name"),
        )
        .select_from(AppointmentModel)
        .join(
            MedicalRecordModel,
            MedicalRecordModel.fk_appointment_id == AppointmentModel.id,
        )
        .join(
            PatientModel,
            PatientModel.id == AppointmentModel.fk_patient_id,
        )
        .join(
            DoctorModel,
            DoctorModel.id == AppointmentModel.fk_doctor_id,
        )
        .where(
            and_(
                AppointmentModel.appointment_date >= start_date,
                AppointmentModel.appointment_date <= end_date,
                AppointmentModel.status == RecordStatus.ACTIVE,
                MedicalRecordModel.status == RecordStatus.ACTIVE,
                MedicalRecordModel.evaluation.isnot(None),
            )
        )
    )

    result = await db.execute(stmt)
    return result.all()

