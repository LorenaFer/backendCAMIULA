"""DTOs del caso de uso de Recetas Médicas."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class PrescriptionItemInputDTO:
    medication_id: str
    quantity_prescribed: int
    dosage_instructions: Optional[str] = None
    duration_days: Optional[int] = None


@dataclass
class CreatePrescriptionDTO:
    fk_appointment_id: str
    fk_patient_id: str
    fk_doctor_id: str
    items: List[PrescriptionItemInputDTO] = field(default_factory=list)
    notes: Optional[str] = None
