from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, time
from typing import Optional
from uuid import uuid4


@dataclass
class DoctorAvailability:
    doctor_id: str
    day_of_week: int
    start_time: time
    end_time: time
    slot_duration: int
    id: str = field(default_factory=lambda: str(uuid4()))

    VALID_DAYS = {1, 2, 3, 4, 5}
    VALID_DURATIONS = {15, 20, 30, 45, 60}

    def validate(self) -> None:
        if self.day_of_week not in self.VALID_DAYS:
            raise ValueError(f"Día inválido: {self.day_of_week}. Debe ser 1-5 (Lun-Vie)")
        if self.slot_duration not in self.VALID_DURATIONS:
            raise ValueError(f"Duración inválida: {self.slot_duration}. Permitidos: {self.VALID_DURATIONS}")
        if self.start_time >= self.end_time:
            raise ValueError("La hora de inicio debe ser anterior a la hora de fin")

    def overlaps_with(self, other: DoctorAvailability) -> bool:
        """Verifica si dos bloques se solapan en el mismo día."""
        if self.day_of_week != other.day_of_week:
            return False
        return self.start_time < other.end_time and other.start_time < self.end_time


@dataclass
class DoctorException:
    doctor_id: str
    exception_date: date
    id: str = field(default_factory=lambda: str(uuid4()))
    reason: Optional[str] = None
