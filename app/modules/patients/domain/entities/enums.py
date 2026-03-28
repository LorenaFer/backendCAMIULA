"""Enums de dominio del módulo patients."""

import enum


class PatientStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
