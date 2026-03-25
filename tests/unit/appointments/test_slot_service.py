"""Tests unitarios para slot_service — lógica pura de dominio."""

from datetime import time

from app.modules.appointments.domain.services.slot_service import (
    generate_slots,
    time_to_minutes,
    minutes_to_time,
    times_overlap,
)


class TestSlotService:
    def test_time_to_minutes(self):
        assert time_to_minutes(time(8, 0)) == 480
        assert time_to_minutes(time(12, 30)) == 750
        assert time_to_minutes(time(0, 0)) == 0

    def test_minutes_to_time(self):
        assert minutes_to_time(480) == time(8, 0)
        assert minutes_to_time(750) == time(12, 30)

    def test_generate_slots_30min(self):
        slots = generate_slots(time(8, 0), time(10, 0), 30)
        assert len(slots) == 4
        assert slots[0]["start"] == time(8, 0)
        assert slots[0]["end"] == time(8, 30)
        assert slots[-1]["start"] == time(9, 30)
        assert slots[-1]["end"] == time(10, 0)

    def test_generate_slots_60min(self):
        slots = generate_slots(time(8, 0), time(12, 0), 60)
        assert len(slots) == 4

    def test_generate_slots_partial(self):
        # 8:00-9:20 con 30 min = 2 slots (8:00-8:30, 8:30-9:00)
        # 9:00-9:20 no cabe otro de 30 min
        slots = generate_slots(time(8, 0), time(9, 20), 30)
        assert len(slots) == 2

    def test_times_overlap_true(self):
        assert times_overlap(time(8, 0), time(9, 0), time(8, 30), time(9, 30)) is True

    def test_times_overlap_false(self):
        assert times_overlap(time(8, 0), time(9, 0), time(9, 0), time(10, 0)) is False

    def test_times_overlap_contained(self):
        assert times_overlap(time(8, 0), time(12, 0), time(9, 0), time(10, 0)) is True
