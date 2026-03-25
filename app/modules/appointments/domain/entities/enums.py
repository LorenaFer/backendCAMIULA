"""Enums de dominio del módulo appointments.

Centralizan los valores válidos de status para evitar magic strings
dispersos en entities, repositories, routes y models.
"""

import enum


class AppointmentStatus(str, enum.Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    ATTENDED = "ATTENDED"
    CANCELLED = "CANCELLED"
    NO_SHOW = "NO_SHOW"

    # Transiciones válidas de la máquina de estados
    _transitions = None

    @classmethod
    def transitions(cls) -> dict:
        return {
            cls.PENDING: {cls.CONFIRMED, cls.CANCELLED},
            cls.CONFIRMED: {cls.ATTENDED, cls.CANCELLED, cls.NO_SHOW},
            cls.ATTENDED: set(),
            cls.CANCELLED: set(),
            cls.NO_SHOW: set(),
        }

    @classmethod
    def schedulable(cls) -> set:
        """Estados que ocupan un slot (no cancelados)."""
        return {cls.PENDING, cls.CONFIRMED}

    @classmethod
    def excluded(cls) -> set:
        """Estados excluidos en filtros por defecto."""
        return {cls.CANCELLED, cls.NO_SHOW}

    # Mapeo español → enum para la capa de presentación
    _DISPLAY_MAP = {
        "pendiente": "PENDING",
        "confirmada": "CONFIRMED",
        "atendida": "ATTENDED",
        "cancelada": "CANCELLED",
        "no_asistio": "NO_SHOW",
    }

    @classmethod
    def from_display(cls, value: str) -> "AppointmentStatus":
        """Convierte nombre en español o inglés al enum."""
        mapped = cls._DISPLAY_MAP.get(value.lower(), value.upper())
        return cls(mapped)

    @property
    def display_name(self) -> str:
        """Nombre en español para respuestas al frontend."""
        reverse = {v: k for k, v in self._DISPLAY_MAP.items()}
        return reverse.get(self.value, self.value.lower())


class DoctorStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
