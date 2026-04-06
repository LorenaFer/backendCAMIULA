"""Pure date utility functions for the Dashboard module.

No SQLAlchemy dependency — these belong in the domain layer.
"""

from datetime import date, timedelta
from typing import Optional, Tuple


def parse_date(value: Optional[str]) -> date:
    """Return a ``date`` from an ISO string or today's date. O(1)."""
    if value:
        return date.fromisoformat(value)
    return date.today()


def period_range(ref_date: date, period: str) -> Tuple[date, date]:
    """Return (start, end) inclusive date range for the given period. O(1)."""
    if period == "week":
        start = ref_date - timedelta(days=ref_date.weekday())
        end = start + timedelta(days=6)
    elif period == "month":
        start = ref_date.replace(day=1)
        next_month = (ref_date.replace(day=28) + timedelta(days=4)).replace(day=1)
        end = next_month - timedelta(days=1)
    elif period == "year":
        start = ref_date.replace(month=1, day=1)
        end = ref_date.replace(month=12, day=31)
    else:
        start = ref_date
        end = ref_date
    return start, end
