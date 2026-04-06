"""Pure domain functions for epidemiological reports.

No SQLAlchemy dependency — these belong in the domain layer.
Used by both infrastructure (query service) and application (use cases).
"""

import calendar
from datetime import date, timedelta
from typing import Tuple

from app.modules.reports.domain.epi_catalogue import AGE_GROUP_BOUNDS, AGE_GROUP_KEYS


def calculate_age(birth_date: date, reference_date: date) -> int:
    """Calculate age in years at reference_date. O(1)."""
    years = reference_date.year - birth_date.year
    if (reference_date.month, reference_date.day) < (birth_date.month, birth_date.day):
        years -= 1
    return max(years, 0)


def get_age_group(age: int) -> str:
    """Map an integer age to the EPI-12 age group key. O(1)."""
    for key, (lo, hi) in zip(AGE_GROUP_KEYS, AGE_GROUP_BOUNDS):
        if lo <= age <= hi:
            return key
    return "65+"


def epi_week_date_range(year: int, week: int) -> Tuple[date, date]:
    """Return (monday, sunday) of the given ISO epidemiological week. O(1)."""
    jan4 = date(year, 1, 4)
    week1_monday = jan4 - timedelta(days=jan4.isoweekday() - 1)
    target_monday = week1_monday + timedelta(weeks=week - 1)
    target_sunday = target_monday + timedelta(days=6)
    return target_monday, target_sunday


def month_date_range(year: int, month: int) -> Tuple[date, date]:
    """Return (first_day, last_day) of the given month. O(1)."""
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

    O(1) for single codes, O(k) for ranges where k = range span.
    """
    if range_str == "*":
        return True

    code_upper = code.upper().strip()

    if "-" not in range_str:
        return code_upper.startswith(range_str.upper())

    parts = range_str.split("-")
    start_str = parts[0].strip().upper()
    end_str = parts[1].strip().upper()

    start_letter = start_str[0]
    end_letter = end_str[0]

    if not code_upper or code_upper[0] < start_letter or code_upper[0] > end_letter:
        return False

    try:
        start_num = int(start_str[1:])
        end_num = int(end_str[1:])
    except ValueError:
        return False

    code_letter = code_upper[0]
    code_num_str = ""
    for ch in code_upper[1:]:
        if ch.isdigit():
            code_num_str += ch
        else:
            break

    if not code_num_str:
        return False

    code_num = int(code_num_str)

    if start_letter == end_letter:
        return code_letter == start_letter and start_num <= code_num <= end_num

    if code_letter == start_letter:
        return code_num >= start_num
    if code_letter == end_letter:
        return code_num <= end_num
    return start_letter < code_letter < end_letter
