"""Tests unitarios para entidades del módulo appointments."""

import pytest
from datetime import date, time, timedelta

from app.modules.appointments.domain.entities.appointment import Appointment
from app.modules.appointments.domain.entities.availability import (
    DoctorAvailability,
    DoctorException,
)
from app.modules.appointments.domain.entities.doctor import Doctor
from app.modules.appointments.domain.entities.medical_record import MedicalRecord
from app.modules.appointments.domain.entities.specialty import Specialty


class TestSpecialtyEntity:
    def test_create(self):
        s = Specialty(name="Medicina General")
        assert s.name == "Medicina General"
        assert len(s.id) == 36


class TestDoctorEntity:
    def test_create(self):
        d = Doctor(
            first_name="Carlos",
            last_name="Mendoza",
            user_id="user-1",
            specialty_id="spec-1",
        )
        assert d.full_name == "Carlos Mendoza"
        assert d.display_name == "Dr. Carlos Mendoza"
        assert d.doctor_status == "ACTIVE"


class TestAvailabilityEntity:
    def test_validate_valid(self):
        block = DoctorAvailability(
            doctor_id="doc-1",
            day_of_week=1,
            start_time=time(8, 0),
            end_time=time(12, 0),
            slot_duration=30,
        )
        block.validate()

    def test_validate_invalid_day(self):
        block = DoctorAvailability(
            doctor_id="doc-1",
            day_of_week=6,
            start_time=time(8, 0),
            end_time=time(12, 0),
            slot_duration=30,
        )
        with pytest.raises(ValueError, match="Día inválido"):
            block.validate()

    def test_validate_invalid_duration(self):
        block = DoctorAvailability(
            doctor_id="doc-1",
            day_of_week=1,
            start_time=time(8, 0),
            end_time=time(12, 0),
            slot_duration=25,
        )
        with pytest.raises(ValueError, match="Duración inválida"):
            block.validate()

    def test_validate_start_after_end(self):
        block = DoctorAvailability(
            doctor_id="doc-1",
            day_of_week=1,
            start_time=time(14, 0),
            end_time=time(8, 0),
            slot_duration=30,
        )
        with pytest.raises(ValueError, match="hora de inicio"):
            block.validate()

    def test_overlap_same_day(self):
        b1 = DoctorAvailability(
            doctor_id="doc-1", day_of_week=1,
            start_time=time(8, 0), end_time=time(12, 0), slot_duration=30,
        )
        b2 = DoctorAvailability(
            doctor_id="doc-1", day_of_week=1,
            start_time=time(10, 0), end_time=time(14, 0), slot_duration=30,
        )
        assert b1.overlaps_with(b2) is True

    def test_no_overlap_different_day(self):
        b1 = DoctorAvailability(
            doctor_id="doc-1", day_of_week=1,
            start_time=time(8, 0), end_time=time(12, 0), slot_duration=30,
        )
        b2 = DoctorAvailability(
            doctor_id="doc-1", day_of_week=2,
            start_time=time(8, 0), end_time=time(12, 0), slot_duration=30,
        )
        assert b1.overlaps_with(b2) is False


class TestAppointmentEntity:
    def _make_appointment(self, **kwargs):
        defaults = dict(
            patient_id="pat-1",
            doctor_id="doc-1",
            specialty_id="spec-1",
            appointment_date=date.today() + timedelta(days=5),
            start_time=time(9, 0),
            end_time=time(9, 30),
            duration_minutes=30,
        )
        defaults.update(kwargs)
        return Appointment(**defaults)

    def test_valid_transition_pending_to_confirmed(self):
        apt = self._make_appointment()
        apt.change_status("CONFIRMED")
        assert apt.appointment_status == "CONFIRMED"

    def test_valid_transition_confirmed_to_attended(self):
        apt = self._make_appointment(appointment_status="CONFIRMED")
        apt.change_status("ATTENDED")
        assert apt.appointment_status == "ATTENDED"

    def test_invalid_transition_pending_to_attended(self):
        apt = self._make_appointment()
        with pytest.raises(ValueError, match="No se puede cambiar"):
            apt.change_status("ATTENDED")

    def test_terminal_state_cannot_change(self):
        apt = self._make_appointment(appointment_status="CANCELLED")
        with pytest.raises(ValueError):
            apt.change_status("CONFIRMED")

    def test_validate_date_too_soon(self):
        apt = self._make_appointment(appointment_date=date.today())
        with pytest.raises(ValueError, match="2 días"):
            apt.validate_date()

    def test_validate_date_ok(self):
        apt = self._make_appointment(
            appointment_date=date.today() + timedelta(days=3)
        )
        apt.validate_date()

    def test_validate_duration_first_visit(self):
        apt = self._make_appointment(is_first_visit=True, duration_minutes=30)
        with pytest.raises(ValueError, match="60 minutos"):
            apt.validate_duration()

    def test_validate_duration_control(self):
        apt = self._make_appointment(is_first_visit=False, duration_minutes=60)
        with pytest.raises(ValueError, match="30 minutos"):
            apt.validate_duration()


class TestMedicalRecordEntity:
    def test_mark_prepared(self):
        record = MedicalRecord(
            appointment_id="apt-1",
            patient_id="pat-1",
            doctor_id="doc-1",
            evaluation={"motivo_consulta": "Control"},
        )
        assert record.is_prepared is False
        record.mark_prepared("user-1")
        assert record.is_prepared is True
        assert record.prepared_by == "user-1"
