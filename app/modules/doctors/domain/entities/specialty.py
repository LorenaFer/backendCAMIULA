"""Domain entity: Specialty."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Specialty:
    id: str
    name: str
    status: Optional[str] = None
    created_at: Optional[str] = None
    created_by: Optional[str] = None
