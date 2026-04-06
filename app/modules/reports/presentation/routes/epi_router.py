"""FastAPI routes for EPI epidemiological reports."""

from __future__ import annotations

import calendar
from datetime import date
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.reports.domain.epi_catalogue import (
    AGE_GROUP_KEYS,
    EPI15_CATALOGUE,
    MONTH_NAMES_EN,
)
from app.modules.reports.infrastructure.epi_query_service import (
    _extract_cie10,
    _extract_disease_name,
    _fetch_records_in_range,
    calculate_age,
    epi_week_date_range,
    get_age_group,
    matches_cie10_range,
    month_date_range,
)
# NOTE: epi_query_service import is an accepted cross-cutting exemption (ADR-003)
from app.shared.database.session import get_db
from app.shared.middleware.auth import get_optional_user_id
from app.shared.schemas.responses import ok

router = APIRouter(prefix="/reports", tags=["Epidemiological Reports"])



@router.get("/epi-12")
async def epi12_weekly_consolidation(
    year: int = Query(..., ge=2000, le=2100, description="Year"),
    week: int = Query(..., ge=1, le=53, description="Epidemiological week (ISO)"),
    db: AsyncSession = Depends(get_db),
    _user_id: str = Depends(get_optional_user_id),
):
    """EPI-12: Weekly epidemiological consolidation by CIE-10, age group, and sex.

    Algorithm complexity:
        - DB query: O(log N + k) with index on appointment_date
        - Python aggregation: O(k) single pass over results
        - Age calculation: O(1) per row
    Total: O(k) where k = records in the epidemiological week.
    """
    start_date, end_date = epi_week_date_range(year, week)
    rows = await _fetch_records_in_range(db, start_date, end_date)

    # Accumulator: {cie10: {disease_name, age_groups: {group: {H: n, M: n}}, total}}
    accumulator: Dict[str, Dict[str, Any]] = {}

    for row in rows:
        appt_date = row[0]
        evaluation = row[1]
        birth_date = row[2]
        sex = row[3]

        cie10 = _extract_cie10(evaluation)
        if not cie10:
            continue

        disease_name = _extract_disease_name(evaluation) or cie10
        cie10_upper = cie10.upper().strip()

        # Initialize entry if new
        if cie10_upper not in accumulator:
            age_groups = {}
            for key in AGE_GROUP_KEYS:
                age_groups[key] = {"H": 0, "M": 0}
            accumulator[cie10_upper] = {
                "disease_name": disease_name,
                "age_groups": age_groups,
                "total": 0,
            }

        entry = accumulator[cie10_upper]

        # Calculate age at appointment date
        if birth_date:
            ref = appt_date if appt_date else end_date
            age = calculate_age(birth_date, ref)
        else:
            age = 0

        group = get_age_group(age)
        sex_key = "H" if sex and sex.upper() == "M" else "M"
        # In Venezuelan medical forms: M = Masculino (male) -> H (Hombre),
        # F = Femenino (female) -> M (Mujer)
        if sex and sex.upper() == "M":
            sex_key = "H"
        elif sex and sex.upper() == "F":
            sex_key = "M"
        else:
            sex_key = "H"  # default

        entry["age_groups"][group][sex_key] += 1
        entry["total"] += 1

    # Build response list sorted by CIE-10 code
    result_list = []
    for cie10_code in sorted(accumulator.keys()):
        entry = accumulator[cie10_code]
        result_list.append({
            "cie10": cie10_code,
            "disease_name": entry["disease_name"],
            "age_groups": entry["age_groups"],
            "total": entry["total"],
        })

    return ok(
        data={
            "year": year,
            "week": week,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "diseases": result_list,
            "total_cases": sum(e["total"] for e in result_list),
        },
        message="EPI-12 weekly consolidation generated",
    )




@router.get("/epi-13")
async def epi13_nominal_listing(
    year: int = Query(..., ge=2000, le=2100, description="Year"),
    week: int = Query(..., ge=1, le=53, description="Epidemiological week (ISO)"),
    db: AsyncSession = Depends(get_db),
    _user_id: str = Depends(get_optional_user_id),
):
    """EPI-13: Nominal listing of individual cases in an epidemiological week.

    Algorithm complexity:
        - DB query: O(log N + k) with index on appointment_date
        - Python mapping: O(k) single pass
    Total: O(k) where k = records in the epidemiological week.
    """
    start_date, end_date = epi_week_date_range(year, week)
    rows = await _fetch_records_in_range(db, start_date, end_date)

    cases = []
    for row in rows:
        appt_date = row[0]
        evaluation = row[1]
        birth_date = row[2]
        sex = row[3]
        first_name = row[4]
        last_name = row[5]
        home_address = row[6]

        cie10 = _extract_cie10(evaluation)
        if not cie10:
            continue

        disease_name = _extract_disease_name(evaluation) or cie10

        age = 0
        if birth_date:
            ref = appt_date if appt_date else end_date
            age = calculate_age(birth_date, ref)

        cases.append({
            "date": appt_date.isoformat() if appt_date else None,
            "patient_name": "{} {}".format(first_name or "", last_name or "").strip(),
            "age": age,
            "sex": sex or "N/A",
            "address": home_address or "N/A",
            "disease": disease_name,
            "cie10": cie10.upper().strip(),
        })

    return ok(
        data={
            "year": year,
            "week": week,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "cases": cases,
            "total_cases": len(cases),
        },
        message="EPI-13 nominal listing generated",
    )




def _build_epi15_structure() -> List[Dict[str, Any]]:
    """Build the nested category -> subcategory -> disease structure.

    Returns a list of categories, each with subcategories and diseases.
    All counts initialized to 0.
    Complexity: O(C) where C = catalogue size (~61 entries).
    """
    categories_order: List[str] = []
    categories_map: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}

    for entry in EPI15_CATALOGUE:
        cat = entry["category"]
        subcat = entry["subcategory"]

        if cat not in categories_map:
            categories_map[cat] = {}
            categories_order.append(cat)

        if subcat not in categories_map[cat]:
            categories_map[cat][subcat] = []

        categories_map[cat][subcat].append({
            "order": entry["order"],
            "name": entry["name"],
            "cie10_range": entry["cie10_range"],
            "count": 0,
            "accumulated": 0,
        })

    result = []
    for cat in categories_order:
        subcats = []
        for subcat_name, diseases in categories_map[cat].items():
            subcats.append({
                "name": subcat_name,
                "diseases": diseases,
            })
        result.append({
            "name": cat,
            "subcategories": subcats,
        })

    return result


async def _count_accumulated(
    db: AsyncSession,
    year: int,
    up_to_month: int,
) -> Dict[str, int]:
    """Count cases from January 1 to end of up_to_month for accumulated totals.

    Complexity: O(log N + k) for the DB query, O(k) for Python aggregation.
    """
    start = date(year, 1, 1)
    _, last_day_num = calendar.monthrange(year, up_to_month)
    end = date(year, up_to_month, last_day_num)

    rows = await _fetch_records_in_range(db, start, end)

    counts: Dict[str, int] = {}
    for row in rows:
        evaluation = row[1]
        cie10 = _extract_cie10(evaluation)
        if not cie10:
            continue
        cie10_upper = cie10.upper().strip()
        counts[cie10_upper] = counts.get(cie10_upper, 0) + 1

    return counts


@router.get("/epi-15")
async def epi15_monthly_morbidity(
    year: int = Query(..., ge=2000, le=2100, description="Year"),
    month: int = Query(..., ge=1, le=12, description="Month (1-12)"),
    db: AsyncSession = Depends(get_db),
    _user_id: str = Depends(get_optional_user_id),
):
    """EPI-15: Monthly morbidity consolidation by MPPS disease catalogue.

    Algorithm complexity:
        - Two DB queries: O(log N + k) each
        - Catalogue matching: O(k * C) where C = catalogue size (~61)
        - Structure building: O(C)
    Total: O(k * C) dominated by matching step.
    """
    start_date, end_date = month_date_range(year, month)

    # Fetch monthly records
    monthly_rows = await _fetch_records_in_range(db, start_date, end_date)

    # Count monthly cases by CIE-10
    monthly_counts: Dict[str, int] = {}
    for row in monthly_rows:
        evaluation = row[1]
        cie10 = _extract_cie10(evaluation)
        if not cie10:
            continue
        cie10_upper = cie10.upper().strip()
        monthly_counts[cie10_upper] = monthly_counts.get(cie10_upper, 0) + 1

    # Fetch accumulated counts (Jan 1 to end of this month)
    accumulated_counts = await _count_accumulated(db, year, month)

    # Build the catalogue structure
    categories = _build_epi15_structure()

    matched_codes: set = set()

    # First pass: assign counts to non-wildcard catalogue entries, track matched codes
    for cat in categories:
        for subcat in cat["subcategories"]:
            for disease in subcat["diseases"]:
                cie10_range = disease["cie10_range"]
                if cie10_range == "*":
                    continue  # handle wildcard in second pass

                disease_count = 0
                disease_accumulated = 0

                for code, count in monthly_counts.items():
                    if matches_cie10_range(code, cie10_range):
                        disease_count += count
                        matched_codes.add(code)

                for code, count in accumulated_counts.items():
                    if matches_cie10_range(code, cie10_range):
                        disease_accumulated += count

                disease["count"] = disease_count
                disease["accumulated"] = disease_accumulated

    # Second pass: "Other causes" (*) gets only unmatched codes
    for cat in categories:
        for subcat in cat["subcategories"]:
            for disease in subcat["diseases"]:
                if disease["cie10_range"] != "*":
                    continue
                other_count = 0
                other_accumulated = 0
                for code, count in monthly_counts.items():
                    if code not in matched_codes:
                        other_count += count
                for code, count in accumulated_counts.items():
                    if code not in matched_codes:
                        other_accumulated += count
                disease["count"] = other_count
                disease["accumulated"] = other_accumulated

    return ok(
        data={
            "year": year,
            "month": month,
            "month_name": MONTH_NAMES_EN[month],
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "categories": categories,
            "total_cases": sum(
                d["count"]
                for cat in categories
                for sub in cat["subcategories"]
                for d in sub["diseases"]
            ),
        },
        message="EPI-15 monthly morbidity consolidation generated",
    )
