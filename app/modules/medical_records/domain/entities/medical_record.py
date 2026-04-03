"""Domain entity: Medical Record."""

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class MedicalRecord:
    id: str
    fk_appointment_id: str
    fk_patient_id: str
    fk_doctor_id: str
    evaluation: Optional[Any] = None
    is_prepared: bool = False
    prepared_at: Optional[str] = None
    prepared_by: Optional[str] = None
    schema_id: Optional[str] = None
    schema_version: Optional[str] = None
    status: str = "A"
    created_at: Optional[str] = None
    created_by: Optional[str] = None
    updated_at: Optional[str] = None
    updated_by: Optional[str] = None
