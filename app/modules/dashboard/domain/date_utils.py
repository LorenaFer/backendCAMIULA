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


def period_range(fecha: date, periodo: str) -> Tuple[date, date]:
    """Return (start, end) inclusive date range for the given period. O(1)."""
    if periodo == "week":
        start = fecha - timedelta(days=fecha.weekday())
        end = start + timedelta(days=6)
    elif periodo == "month":
        start = fecha.replace(day=1)
        next_month = (fecha.replace(day=28) + timedelta(days=4)).replace(day=1)
        end = next_month - timedelta(days=1)
    elif periodo == "year":
        start = fecha.replace(month=1, day=1)
        end = fecha.replace(month=12, day=31)
    else:
        start = fecha
        end = fecha
    return start, end
