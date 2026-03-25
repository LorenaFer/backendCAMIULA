from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Dict, Optional
from uuid import uuid4

from app.modules.patients.domain.entities.enums import PatientStatus


@dataclass
class Patient:
    first_name: str
    last_name: str
    cedula: str
    university_relation: str
    id: str = field(default_factory=lambda: str(uuid4()))
    nhm: Optional[int] = None
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
    is_new: bool = True
    patient_status: str = PatientStatus.ACTIVE.value
    created_at: Optional[datetime] = None

    VALID_RELATIONS = {"empleado", "estudiante", "profesor", "obrero", "tercero"}
    VALID_FAMILY_RELATIONS = {"hijo", "padre", "madre", "conyuge", "otro"}

    def validate_tercero(self) -> None:
        """Valida que un paciente tercero tenga parentesco y titular."""
        if self.university_relation == "tercero":
            if not self.family_relationship:
                raise ValueError("Parentesco es obligatorio para familiares (tercero)")
            if not self.holder_patient_id:
                raise ValueError("Titular (holder_patient_id) es obligatorio para familiares (tercero)")
            if self.family_relationship not in self.VALID_FAMILY_RELATIONS:
                raise ValueError(f"Parentesco inválido: {self.family_relationship}")

    @property
    def age(self) -> Optional[int]:
        """Calcula la edad a partir de fecha de nacimiento."""
        if self.birth_date is None:
            return None
        today = date.today()
        return today.year - self.birth_date.year - (
            (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
        )
