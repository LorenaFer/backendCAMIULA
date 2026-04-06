"""DTOs for Medical Records use cases."""

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class UpsertMedicalRecordDTO:
    fk_appointment_id: str
    fk_patient_id: str
    fk_doctor_id: str
    evaluation: Optional[Any] = None
    schema_id: Optional[str] = None
    schema_version: Optional[str] = None


@dataclass
class UpsertFormSchemaDTO:
    specialty_id: str
    specialty_name: str
    version: str
    schema_json: Optional[Any] = None
