from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, time, timedelta
from typing import Optional
from uuid import uuid4


@dataclass
class Appointment:
    patient_id: str
    doctor_id: str
    specialty_id: str
    appointment_date: date
    start_time: time
    end_time: time
    duration_minutes: int
    is_first_visit: bool = False
    reason: Optional[str] = None
    observations: Optional[str] = None
    appointment_status: str = "PENDING"
    id: str = field(default_factory=lambda: str(uuid4()))
    created_by: Optional[str] = None
    created_at: Optional[str] = None
    # Datos resueltos para respuestas con JOIN
    patient_data: Optional[dict] = None
    doctor_data: Optional[dict] = None

    VALID_TRANSITIONS = {
        "PENDING": {"CONFIRMED", "CANCELLED"},
        "CONFIRMED": {"ATTENDED", "CANCELLED", "NO_SHOW"},
        "ATTENDED": set(),
        "CANCELLED": set(),
        "NO_SHOW": set(),
    }

    def change_status(self, new_status: str) -> None:
        """Cambia el estado respetando las transiciones válidas."""
        allowed = self.VALID_TRANSITIONS.get(self.appointment_status, set())
        if new_status not in allowed:
            raise ValueError(
                f"No se puede cambiar de '{self.appointment_status}' a '{new_status}'. "
                f"Transiciones válidas: {allowed or 'ninguna (estado terminal)'}"
            )
        self.appointment_status = new_status

    def validate_date(self) -> None:
        """Valida que la fecha sea al menos 2 días en el futuro."""
        min_date = date.today() + timedelta(days=2)
        if self.appointment_date < min_date:
            raise ValueError(
                f"La fecha debe ser al menos 2 días en el futuro (mínimo: {min_date})"
            )

    def validate_duration(self) -> None:
        """Valida que la duración corresponda al tipo de visita."""
        expected = 60 if self.is_first_visit else 30
        if self.duration_minutes != expected:
            raise ValueError(
                f"La duración debe ser {expected} minutos para "
                f"{'primera vez' if self.is_first_visit else 'control'}"
            )
