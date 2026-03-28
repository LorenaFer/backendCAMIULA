from __future__ import annotations
from abc import ABC, abstractmethod
from datetime import date, time
from typing import Any, Dict, List, Optional, Tuple
from app.modules.appointments.domain.entities.appointment import Appointment


class AppointmentRepository(ABC):
    @abstractmethod
    async def create(self, appointment: Appointment) -> Appointment:
        ...

    @abstractmethod
    async def get_by_id(self, appointment_id: str) -> Optional[Appointment]:
        ...

    @abstractmethod
    async def get_detail(self, appointment_id: str) -> Optional[Appointment]:
        """Obtiene cita con datos de paciente y doctor (JOIN)."""
        ...

    @abstractmethod
    async def list_filtered(
        self,
        page: int,
        page_size: int,
        fecha: Optional[date] = None,
        doctor_id: Optional[str] = None,
        specialty_id: Optional[str] = None,
        estado: Optional[str] = None,
        q: Optional[str] = None,
        mes: Optional[str] = None,
        excluir_canceladas: bool = False,
    ) -> Tuple[List[Appointment], int]:
        ...

    @abstractmethod
    async def update_status(self, appointment_id: str, new_status: str, updated_by: str) -> None:
        ...

    @abstractmethod
    async def is_slot_occupied(
        self, doctor_id: str, appointment_date: date, start_time: time, end_time: time,
        exclude_id: Optional[str] = None
    ) -> bool:
        ...

    @abstractmethod
    async def get_stats(
        self,
        fecha: Optional[date] = None,
        doctor_id: Optional[str] = None,
        specialty_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Estadísticas agregadas de citas para el dashboard."""
        ...
