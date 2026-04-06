"""Domain entity: Form Schema."""

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class FormSchema:
    id: str
    specialty_id: str
    specialty_name: str
    version: str
    schema_json: Optional[Any] = None
    status: str = "A"
    created_at: Optional[str] = None
    created_by: Optional[str] = None
    updated_at: Optional[str] = None
    updated_by: Optional[str] = None
