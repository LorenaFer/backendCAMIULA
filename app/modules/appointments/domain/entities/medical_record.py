from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4


@dataclass
class MedicalRecord:
    appointment_id: str
    patient_id: str
    doctor_id: str
    evaluation: Dict[str, Any]
    id: str = field(default_factory=lambda: str(uuid4()))
    schema_id: Optional[str] = None
    schema_version: Optional[str] = None
    is_prepared: bool = False
    prepared_at: Optional[datetime] = None
    prepared_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def mark_prepared(self, prepared_by: str) -> None:
        """Marca la historia como preparada."""
        self.is_prepared = True
        self.prepared_by = prepared_by
