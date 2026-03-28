"""TDD — Patient medical history use case."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime


def make_record(id="rec-1", appointment_id="apt-1", patient_id="pat-1"):
    from app.modules.appointments.domain.entities.medical_record import MedicalRecord
    return MedicalRecord(
        id=id,
        appointment_id=appointment_id,
        patient_id=patient_id,
        doctor_id="doc-1",
        evaluation={"motivo_consulta": "Control"},
        created_at=datetime(2026, 3, 20),
    )


class TestGetPatientMedicalHistoryUseCase:
    @pytest.mark.asyncio
    async def test_returns_list(self):
        from app.modules.appointments.application.use_cases.get_patient_medical_history import (
            GetPatientMedicalHistoryUseCase,
        )
        repo = MagicMock()
        repo.get_patient_history = AsyncMock(
            return_value=[make_record("r1", "apt-1"), make_record("r2", "apt-2")]
        )

        uc = GetPatientMedicalHistoryUseCase(medical_record_repo=repo)
        result = await uc.execute("pat-1", limit=5)

        assert len(result) == 2
        repo.get_patient_history.assert_called_once_with(
            patient_id="pat-1", limit=5, exclude_appointment_id=None
        )

    @pytest.mark.asyncio
    async def test_passes_exclude_appointment(self):
        from app.modules.appointments.application.use_cases.get_patient_medical_history import (
            GetPatientMedicalHistoryUseCase,
        )
        repo = MagicMock()
        repo.get_patient_history = AsyncMock(return_value=[])

        uc = GetPatientMedicalHistoryUseCase(medical_record_repo=repo)
        await uc.execute("pat-1", limit=5, exclude_appointment_id="apt-99")

        repo.get_patient_history.assert_called_once_with(
            patient_id="pat-1", limit=5, exclude_appointment_id="apt-99"
        )

    @pytest.mark.asyncio
    async def test_empty_history(self):
        from app.modules.appointments.application.use_cases.get_patient_medical_history import (
            GetPatientMedicalHistoryUseCase,
        )
        repo = MagicMock()
        repo.get_patient_history = AsyncMock(return_value=[])

        uc = GetPatientMedicalHistoryUseCase(medical_record_repo=repo)
        result = await uc.execute("pat-99", limit=5)

        assert result == []
