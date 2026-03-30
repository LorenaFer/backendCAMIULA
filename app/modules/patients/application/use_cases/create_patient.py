"""Caso de uso: crear paciente."""

from app.core.exceptions import ConflictException
from app.modules.patients.application.dtos.patient_dto import CreatePatientDTO
from app.modules.patients.domain.entities.patient import Patient
from app.modules.patients.domain.repositories.patient_repository import PatientRepository

ULA_RELATION_MAP = {
    "P": "profesor",
    "E": "empleado",
    "B": "estudiante",
    "O": "tercero",
    "F": "tercero",
    "C": "tercero",
    "R": "tercero",
    "S": "tercero",
    "T": "tercero",
    "X": "tercero",
}

ALLOWED_RELATIONS = {"empleado", "estudiante", "profesor", "tercero"}


def normalize_relacion_univ(value: str | None) -> str:
    if not value:
        return "tercero"

    raw = value.strip()
    if not raw:
        return "tercero"

    upper = raw.upper()
    if upper in ULA_RELATION_MAP:
        return ULA_RELATION_MAP[upper]

    normalized = raw.lower()
    return normalized if normalized in ALLOWED_RELATIONS else "tercero"


class CreatePatient:

    def __init__(self, repo: PatientRepository) -> None:
        self._repo = repo

    async def execute(self, dto: CreatePatientDTO, created_by: str) -> Patient:
        existing = await self._repo.find_by_cedula(dto.cedula)
        if existing:
            raise ConflictException("Ya existe un paciente con esa cédula")

        nhm = await self._repo.get_next_nhm()

        data = {
            "nhm": nhm,
            "cedula": dto.cedula,
            "nombre": dto.nombre,
            "apellido": dto.apellido,
            "sexo": dto.sexo,
            "fecha_nacimiento": dto.fecha_nacimiento,
            "lugar_nacimiento": dto.lugar_nacimiento,
            "edad": dto.edad,
            "estado_civil": dto.estado_civil,
            "religion": dto.religion,
            "procedencia": dto.procedencia,
            "direccion_habitacion": dto.direccion_habitacion,
            "telefono": dto.telefono,
            "profesion": dto.profesion,
            "ocupacion_actual": dto.ocupacion_actual,
            "direccion_trabajo": dto.direccion_trabajo,
            "clasificacion_economica": dto.clasificacion_economica,
            "relacion_univ": normalize_relacion_univ(dto.relacion_univ),
            "parentesco": dto.parentesco,
            "titular_nhm": dto.titular_nhm,
            "datos_medicos": dto.datos_medicos or {},
            "contacto_emergencia": dto.contacto_emergencia or {},
            "es_nuevo": True,
            "patient_status": "active",
        }
        return await self._repo.create(data, created_by)
