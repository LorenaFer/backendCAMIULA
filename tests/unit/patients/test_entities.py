"""Tests unitarios para entidades del módulo patients."""

import pytest

from app.modules.patients.domain.entities.patient import Patient


class TestPatientEntity:
    def test_create_patient(self):
        patient = Patient(
            first_name="Maria",
            last_name="Garcia",
            cedula="V-12345678",
            university_relation="empleado",
        )
        assert patient.first_name == "Maria"
        assert patient.last_name == "Garcia"
        assert patient.cedula == "V-12345678"
        assert patient.university_relation == "empleado"
        assert len(patient.id) == 36
        assert patient.is_new is True
        assert patient.nhm is None

    def test_validate_tercero_missing_parentesco(self):
        patient = Patient(
            first_name="Ana",
            last_name="Lopez",
            cedula="V-11111111",
            university_relation="tercero",
            holder_patient_id="some-id",
        )
        with pytest.raises(ValueError, match="Parentesco es obligatorio"):
            patient.validate_tercero()

    def test_validate_tercero_missing_holder(self):
        patient = Patient(
            first_name="Ana",
            last_name="Lopez",
            cedula="V-11111111",
            university_relation="tercero",
            family_relationship="hijo",
        )
        with pytest.raises(ValueError, match="Titular"):
            patient.validate_tercero()

    def test_validate_tercero_invalid_parentesco(self):
        patient = Patient(
            first_name="Ana",
            last_name="Lopez",
            cedula="V-11111111",
            university_relation="tercero",
            family_relationship="primo",
            holder_patient_id="some-id",
        )
        with pytest.raises(ValueError, match="Parentesco inválido"):
            patient.validate_tercero()

    def test_validate_tercero_valid(self):
        patient = Patient(
            first_name="Ana",
            last_name="Lopez",
            cedula="V-11111111",
            university_relation="tercero",
            family_relationship="hijo",
            holder_patient_id="some-id",
        )
        patient.validate_tercero()  # No error

    def test_validate_non_tercero_skips(self):
        patient = Patient(
            first_name="Maria",
            last_name="Garcia",
            cedula="V-12345678",
            university_relation="empleado",
        )
        patient.validate_tercero()  # No error

    def test_age_calculation(self):
        from datetime import date

        patient = Patient(
            first_name="Test",
            last_name="User",
            cedula="V-00000001",
            university_relation="estudiante",
            birth_date=date(1990, 1, 1),
        )
        assert patient.age is not None
        assert patient.age >= 36

    def test_age_none_without_birthdate(self):
        patient = Patient(
            first_name="Test",
            last_name="User",
            cedula="V-00000001",
            university_relation="estudiante",
        )
        assert patient.age is None

    def test_valid_relations(self):
        assert "empleado" in Patient.VALID_RELATIONS
        assert "estudiante" in Patient.VALID_RELATIONS
        assert "profesor" in Patient.VALID_RELATIONS
        assert "obrero" in Patient.VALID_RELATIONS
        assert "tercero" in Patient.VALID_RELATIONS
