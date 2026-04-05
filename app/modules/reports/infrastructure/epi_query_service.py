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



def calculate_age(birth_date: date, reference_date: date) -> int:
    """Calculate age in years at reference_date.

    Complexity: O(1).
    """
    years = reference_date.year - birth_date.year
    if (reference_date.month, reference_date.day) < (birth_date.month, birth_date.day):
        years -= 1
    return max(years, 0)


def get_age_group(age: int) -> str:
    """Map an integer age to the EPI-12 age group key.

    Uses a linear scan over 12 fixed-size buckets -> O(1).
    """
    for key, (lo, hi) in zip(AGE_GROUP_KEYS, AGE_GROUP_BOUNDS):
        if lo <= age <= hi:
            return key
    return "65+"


def epi_week_date_range(year: int, week: int) -> Tuple[date, date]:
    """Return (monday, sunday) of the given ISO epidemiological week.

    ISO 8601: week 1 contains Jan 4th.
    Complexity: O(1).
    """
    # Jan 4th always belongs to ISO week 1
    jan4 = date(year, 1, 4)
    # Monday of ISO week 1
    week1_monday = jan4 - timedelta(days=jan4.isoweekday() - 1)
    # Target week monday
    target_monday = week1_monday + timedelta(weeks=week - 1)
    target_sunday = target_monday + timedelta(days=6)
    return target_monday, target_sunday


def month_date_range(year: int, month: int) -> Tuple[date, date]:
    """Return (first_day, last_day) of the given month.

    Complexity: O(1).
    """
    first_day = date(year, month, 1)
    last_day_num = calendar.monthrange(year, month)[1]
    last_day = date(year, month, last_day_num)
    return first_day, last_day


def matches_cie10_range(code: str, range_str: str) -> bool:
    """Check if a CIE-10 code matches a catalogue range definition.

    Supported formats:
        "A00"       -> code starts with "A00"
        "A08-A09"   -> code starts with A08 or A09
        "A17-A19"   -> code starts with A17, A18, or A19
        "S02-S92"   -> code letter+number prefix in range
        "*"         -> matches everything (catch-all)

    Complexity: O(1) for single codes, O(k) for ranges where k = range span.
    """
    if range_str == "*":
        return True

    code_upper = code.upper().strip()

    if "-" not in range_str:
        # Single code: prefix match
        return code_upper.startswith(range_str.upper())

    # Range: "X##-Y##"
    parts = range_str.split("-")
    start_str = parts[0].strip().upper()
    end_str = parts[1].strip().upper()

    # Extract letter prefix and numeric part
    start_letter = start_str[0]
    end_letter = end_str[0]

    # Simple case: same letter prefix (e.g., A08-A09, A17-A19)
    if start_letter == end_letter:
        try:
            start_num = int(start_str[1:])
            end_num = int(end_str[1:])
        except ValueError:
            return code_upper.startswith(start_str) or code_upper.startswith(end_str)

        if not code_upper or code_upper[0] != start_letter:
            return False

        # Extract numeric prefix from the code (e.g., "A09.1" -> 9)
        code_num_str = ""
        for ch in code_upper[1:]:
            if ch.isdigit():
                code_num_str += ch
            else:
                break

        if not code_num_str:
            return False

        code_num = int(code_num_str)
        return start_num <= code_num <= end_num

    # Cross-letter range (e.g., S02-S92 is same letter, but handle
    # edge case like B20-B24). For different letters, expand.
    # Since most MPPS ranges use the same letter, do prefix matching
    # for both endpoints as a fallback.
    return code_upper.startswith(start_str) or code_upper.startswith(end_str)


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

