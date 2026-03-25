from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, time, timedelta
from typing import Optional
from uuid import uuid4

from app.modules.appointments.domain.entities.enums import AppointmentStatus


@dataclass
class AppointmentJoinData:
    """Datos resueltos de paciente/doctor para respuestas con JOIN."""

    patient_id: str = ""
    patient_nhm: int = 0
    patient_first_name: str = ""
    patient_last_name: str = ""
    patient_cedula: str = ""
    patient_university_relation: str = ""
    doctor_id: str = ""
    doctor_first_name: str = ""
    doctor_last_name: str = ""
    specialty_name: str = ""


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
    appointment_status: AppointmentStatus = AppointmentStatus.PENDING
    id: str = field(default_factory=lambda: str(uuid4()))
    created_by: Optional[str] = None
    created_at: Optional[str] = None
    join_data: Optional[AppointmentJoinData] = None

    def change_status(self, new_status: AppointmentStatus) -> None:
        """Cambia el estado respetando las transiciones válidas."""
        if isinstance(new_status, str):
            new_status = AppointmentStatus(new_status)
        allowed = AppointmentStatus.transitions().get(self.appointment_status, set())
        if new_status not in allowed:
            raise ValueError(
                f"No se puede cambiar de '{self.appointment_status.value}' a '{new_status.value}'. "
                f"Transiciones válidas: {', '.join(s.value for s in allowed) or 'ninguna (estado terminal)'}"
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
