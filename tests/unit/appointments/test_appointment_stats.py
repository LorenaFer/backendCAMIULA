"""TDD — Appointment Stats use case."""

import pytest
from unittest.mock import AsyncMock, MagicMock


class TestGetAppointmentStatsUseCase:
    @pytest.mark.asyncio
    async def test_returns_stats_dict(self):
        from app.modules.appointments.application.use_cases.get_appointment_stats import (
            GetAppointmentStatsUseCase,
        )
        repo = MagicMock()
        fake_stats = {
            "total": 10,
            "byStatus": {"PENDING": 3, "CONFIRMED": 5, "ATTENDED": 2},
            "bySpecialty": [],
            "byDoctor": [],
            "firstTimeCount": 4,
            "returningCount": 6,
            "byPatientType": {},
            "dailyTrend": [],
            "peakHours": [],
        }
        repo.get_stats = AsyncMock(return_value=fake_stats)

        uc = GetAppointmentStatsUseCase(appointment_repo=repo)
        result = await uc.execute()

        assert result["total"] == 10
        assert "byStatus" in result
        repo.get_stats.assert_called_once()

    @pytest.mark.asyncio
    async def test_passes_filters_to_repo(self):
        from app.modules.appointments.application.use_cases.get_appointment_stats import (
            GetAppointmentStatsUseCase,
        )
        from datetime import date

        repo = MagicMock()
        repo.get_stats = AsyncMock(return_value={"total": 0})

        uc = GetAppointmentStatsUseCase(appointment_repo=repo)
        await uc.execute(fecha=date(2026, 3, 27), doctor_id="doc-1")

        repo.get_stats.assert_called_once_with(
            fecha=date(2026, 3, 27),
            doctor_id="doc-1",
            specialty_id=None,
        )
