from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class CreatePatientDTO:
    cedula: str
    first_name: str
    last_name: str
    university_relation: str
    sex: Optional[str] = None
    birth_date: Optional[date] = None
    birth_place: Optional[str] = None
    marital_status: Optional[str] = None
    religion: Optional[str] = None
    origin: Optional[str] = None
    home_address: Optional[str] = None
    phone: Optional[str] = None
    profession: Optional[str] = None
    current_occupation: Optional[str] = None
    work_address: Optional[str] = None
    economic_classification: Optional[str] = None
    family_relationship: Optional[str] = None
    holder_patient_id: Optional[str] = None
    medical_data: Optional[Dict[str, Any]] = None
    emergency_contact: Optional[Dict[str, Any]] = None
