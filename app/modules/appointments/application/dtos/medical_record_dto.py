from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class UpsertMedicalRecordDTO:
    appointment_id: str
    patient_id: str
    doctor_id: str
    evaluation: Dict[str, Any]
