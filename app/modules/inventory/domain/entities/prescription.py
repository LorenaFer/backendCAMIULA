"""Entidad de dominio: Receta médica y sus ítems."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class PrescriptionItem:
    id: str
    fk_prescription_id: str
    fk_medication_id: str
    quantity_prescribed: int
    quantity_dispatched: int
    item_status: str
    dosage_instructions: Optional[str] = None
    duration_days: Optional[int] = None


@dataclass
class Prescription:
    id: str
    fk_appointment_id: str
    fk_patient_id: str
    fk_doctor_id: str
    prescription_number: str
    prescription_date: str
    prescription_status: str
    items: List[PrescriptionItem] = field(default_factory=list)
    notes: Optional[str] = None
    created_at: Optional[str] = None
    created_by: Optional[str] = None
