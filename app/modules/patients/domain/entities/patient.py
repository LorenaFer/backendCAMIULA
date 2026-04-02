"""Domain entity: Patient."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Patient:
    id: str
    cedula: str
    nhm: int
    first_name: str
    last_name: str
    university_relation: str
    is_new: bool
    sex: Optional[str] = None
    birth_date: Optional[str] = None
    birth_place: Optional[str] = None
    age: Optional[int] = None
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
    fk_holder_patient_id: Optional[str] = None
    medical_data: dict = field(default_factory=dict)
    emergency_contact: Optional[dict] = None
    patient_status: str = "active"
    created_at: Optional[str] = None
    created_by: Optional[str] = None
