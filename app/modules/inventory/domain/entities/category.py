"""Domain entity: Medication Category."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class MedicationCategory:
    id: str
    name: str
    description: Optional[str] = None
    created_at: Optional[str] = None
    created_by: Optional[str] = None
