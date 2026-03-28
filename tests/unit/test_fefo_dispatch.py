"""Pruebas unitarias para la lógica FEFO de despacho.

Validan que:
1. Los lotes se consumen en orden expiration_date ASC (primero el más próximo a vencer).
2. El límite mensual bloquea el despacho con ForbiddenException(code="LIMIT_EXCEEDED").
3. Una DispatchException activa permite superar el límite mensual.
4. Stock insuficiente lanza InsufficientStockException.
"""

import asyncio
from typing import Optional
from unittest.mock import AsyncMock

import pytest

from app.core.exceptions import ForbiddenException, InsufficientStockException, NotFoundException
from app.modules.inventory.application.use_cases.dispatches.execute_dispatch import (
    execute_dispatch,
)
from app.modules.inventory.application.use_cases.dispatches.validate_and_prepare_dispatch import (
    validate_and_prepare_dispatch,
)
from app.modules.inventory.domain.entities.batch import Batch
from app.modules.inventory.domain.entities.dispatch import Dispatch, DispatchItem
from app.modules.inventory.domain.entities.dispatch_limit import DispatchException, DispatchLimit
from app.modules.inventory.domain.entities.medication import Medication
from app.modules.inventory.domain.entities.prescription import Prescription, PrescriptionItem

# ──────────────────────────────────────────────────────────
# Fixtures de datos espejo del seeder
# ──────────────────────────────────────────────────────────

_PATIENT_ID = "patient-001"
_MED_AMOX_ID = "med-amoxicilina"
_PRESCRIPTION_ID = "rx-001"

# Lote NEAR: vence 2026-05-15 (se debe consumir primero)
_BATCH_NEAR = Batch(
    id="batch-near",
    fk_medication_id=_MED_AMOX_ID,
    lot_number="LOT-2026-AMX-001",
    expiration_date="2026-05-15",
    quantity_received=100,
    quantity_available=100,
    received_at="2026-01-01",
    batch_status="available",
)

# Lote FAR: vence 2027-12-31
_BATCH_FAR = Batch(
    id="batch-far",
    fk_medication_id=_MED_AMOX_ID,
    lot_number="LOT-2026-AMX-002",
    expiration_date="2027-12-31",
    quantity_received=200,
    quantity_available=200,
    received_at="2026-01-01",
    batch_status="available",
)

_PRESCRIPTION_ITEM = PrescriptionItem(
    id="item-001",
    fk_prescription_id=_PRESCRIPTION_ID,
    fk_medication_id=_MED_AMOX_ID,
    quantity_prescribed=42,
    quantity_dispatched=0,
    item_status="active",
)

_PRESCRIPTION = Prescription(
    id=_PRESCRIPTION_ID,
    fk_appointment_id="appt-001",
    fk_patient_id=_PATIENT_ID,
    fk_doctor_id="doc-001",
    prescription_number="PRX-2026-0001",
    prescription_date="2026-03-01",
    prescription_status="active",
    items=[_PRESCRIPTION_ITEM],
)

_LIMIT_42 = DispatchLimit(
    id="limit-001",
    fk_medication_id=_MED_AMOX_ID,
    monthly_max_quantity=42,
    applies_to="all",
    active=True,
)

_MEDICATION = Medication(
    id=_MED_AMOX_ID,
    code="AMX-500",
    generic_name="Amoxicilina 500mg",
    pharmaceutical_form="Cápsulas",
    unit_measure="cápsulas",
    controlled_substance=False,
    requires_refrigeration=False,
    medication_status="active",
)


# ──────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────

def _mock_repos(
    batches=None,
    monthly_used=0,
    limit=None,
    exception=None,
    prescription=None,
):
    if batches is None:
        batches = [_BATCH_NEAR, _BATCH_FAR]
    if prescription is None:
        prescription = _PRESCRIPTION

    prescription_repo = AsyncMock()
    prescription_repo.find_by_id.return_value = prescription
    prescription_repo.update_status = AsyncMock()
    prescription_repo.update_item_dispatched = AsyncMock()

    batch_repo = AsyncMock()
    batch_repo.find_available_fefo.return_value = batches
    batch_repo.find_by_id.side_effect = lambda bid: next(
        (b for b in batches if b.id == bid), None
    )
    batch_repo.update_quantity = AsyncMock()

    dispatch_repo = AsyncMock()
    dispatch_repo.get_monthly_consumption.return_value = monthly_used
    dispatch_repo.create.return_value = Dispatch(
        id="dispatch-001",
        fk_prescription_id=_PRESCRIPTION_ID,
        fk_patient_id=_PATIENT_ID,
        fk_pharmacist_id="pharmacist-001",
        dispatch_date="2026-03-26T00:00:00+00:00",
        dispatch_status="completed",
        items=[
            DispatchItem(
                id="di-001",
                fk_dispatch_id="dispatch-001",
                fk_batch_id="batch-near",
                fk_medication_id=_MED_AMOX_ID,
                quantity_dispatched=42,
            )
        ],
    )

    limit_repo = AsyncMock()
    limit_repo.find_active_limit.return_value = limit
    limit_repo.find_active_exception.return_value = exception

    medication_repo = AsyncMock()
    medication_repo.find_by_id.return_value = _MEDICATION

    return prescription_repo, batch_repo, dispatch_repo, limit_repo, medication_repo


# ──────────────────────────────────────────────────────────
# Tests de validación (validate_and_prepare_dispatch)
# ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_validate_fefo_order():
    """Los lotes se deben listar en orden FEFO (near antes que far)."""
    p_repo, b_repo, d_repo, l_repo, m_repo = _mock_repos(
        batches=[_BATCH_NEAR, _BATCH_FAR],
        monthly_used=0,
        limit=None,
    )

    result = await validate_and_prepare_dispatch(
        prescription_id=_PRESCRIPTION_ID,
        patient_type="all",
        prescription_repo=p_repo,
        batch_repo=b_repo,
        dispatch_repo=d_repo,
        limit_repo=l_repo,
        medication_repo=m_repo,
    )

    assert result.can_dispatch is True
    assert len(result.items) == 1
    item = result.items[0]
    assert item.quantity_available == 300  # 100 + 200
    assert item.can_dispatch is True
    assert item.block_reason is None


@pytest.mark.asyncio
async def test_validate_insufficient_stock():
    """Stock insuficiente → can_dispatch=False con block_reason."""
    p_repo, b_repo, d_repo, l_repo, m_repo = _mock_repos(
        batches=[],  # sin stock
        monthly_used=0,
        limit=None,
    )

    result = await validate_and_prepare_dispatch(
        prescription_id=_PRESCRIPTION_ID,
        patient_type="all",
        prescription_repo=p_repo,
        batch_repo=b_repo,
        dispatch_repo=d_repo,
        limit_repo=l_repo,
        medication_repo=m_repo,
    )

    assert result.can_dispatch is False
    assert result.items[0].can_dispatch is False
    assert "insuficiente" in result.items[0].block_reason.lower()


@pytest.mark.asyncio
async def test_validate_limit_exceeded_no_exception():
    """Límite mensual ya consumido → can_dispatch=False."""
    p_repo, b_repo, d_repo, l_repo, m_repo = _mock_repos(
        monthly_used=42,  # ya usó el límite completo
        limit=_LIMIT_42,
        exception=None,
    )

    result = await validate_and_prepare_dispatch(
        prescription_id=_PRESCRIPTION_ID,
        patient_type="all",
        prescription_repo=p_repo,
        batch_repo=b_repo,
        dispatch_repo=d_repo,
        limit_repo=l_repo,
        medication_repo=m_repo,
    )

    assert result.can_dispatch is False
    assert "límite" in result.items[0].block_reason.lower()


@pytest.mark.asyncio
async def test_validate_limit_exceeded_with_exception_allows():
    """Con excepción activa de 100 unidades, un consumo de 42+42=84 ≤ 100 pasa."""
    active_exception = DispatchException(
        id="exc-001",
        fk_patient_id=_PATIENT_ID,
        fk_medication_id=_MED_AMOX_ID,
        authorized_quantity=100,
        valid_from="2026-01-01",
        valid_until="2026-12-31",
        reason="Tratamiento prolongado",
    )

    p_repo, b_repo, d_repo, l_repo, m_repo = _mock_repos(
        monthly_used=42,
        limit=_LIMIT_42,
        exception=active_exception,
    )

    result = await validate_and_prepare_dispatch(
        prescription_id=_PRESCRIPTION_ID,
        patient_type="all",
        prescription_repo=p_repo,
        batch_repo=b_repo,
        dispatch_repo=d_repo,
        limit_repo=l_repo,
        medication_repo=m_repo,
    )

    assert result.can_dispatch is True
    assert result.items[0].has_exception is True


# ──────────────────────────────────────────────────────────
# Tests de ejecución (execute_dispatch)
# ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_execute_fefo_consumes_near_batch_first():
    """FEFO: batch-near (2026-05-15) debe consumirse antes que batch-far."""
    updated_prescription = Prescription(
        id=_PRESCRIPTION_ID,
        fk_appointment_id="appt-001",
        fk_patient_id=_PATIENT_ID,
        fk_doctor_id="doc-001",
        prescription_number="PRX-2026-0001",
        prescription_date="2026-03-01",
        prescription_status="dispensed",
        items=[
            PrescriptionItem(
                id="item-001",
                fk_prescription_id=_PRESCRIPTION_ID,
                fk_medication_id=_MED_AMOX_ID,
                quantity_prescribed=42,
                quantity_dispatched=42,
                item_status="dispensed",
            )
        ],
    )

    p_repo, b_repo, d_repo, l_repo, _ = _mock_repos(
        batches=[_BATCH_NEAR, _BATCH_FAR],
        monthly_used=0,
        limit=None,
    )
    # Segunda llamada a find_by_id retorna el estado actualizado
    p_repo.find_by_id.side_effect = [_PRESCRIPTION, updated_prescription]

    dispatch = await execute_dispatch(
        fk_prescription_id=_PRESCRIPTION_ID,
        fk_pharmacist_id="pharmacist-001",
        patient_type="all",
        notes=None,
        pharmacist_id="pharmacist-001",
        prescription_repo=p_repo,
        batch_repo=b_repo,
        dispatch_repo=d_repo,
        limit_repo=l_repo,
    )

    # Verificar que update_quantity se llamó para batch-near
    update_calls = b_repo.update_quantity.call_args_list
    batch_ids_updated = [call.args[0] for call in update_calls]
    assert "batch-near" in batch_ids_updated

    # batch-near tiene 100 unidades; se toman 42 → nuevo qty = 58
    near_call = next(c for c in update_calls if c.args[0] == "batch-near")
    assert near_call.args[1] == 58

    # batch-far NO debe haberse tocado (42 ≤ 100 disponibles en near)
    assert "batch-far" not in batch_ids_updated


@pytest.mark.asyncio
async def test_execute_raises_limit_exceeded():
    """Límite mensual excedido sin excepción → ForbiddenException LIMIT_EXCEEDED."""
    p_repo, b_repo, d_repo, l_repo, _ = _mock_repos(
        monthly_used=42,
        limit=_LIMIT_42,
        exception=None,
    )

    with pytest.raises(ForbiddenException) as exc_info:
        await execute_dispatch(
            fk_prescription_id=_PRESCRIPTION_ID,
            fk_pharmacist_id="pharmacist-001",
            patient_type="all",
            notes=None,
            pharmacist_id="pharmacist-001",
            prescription_repo=p_repo,
            batch_repo=b_repo,
            dispatch_repo=d_repo,
            limit_repo=l_repo,
        )

    assert exc_info.value.code == "LIMIT_EXCEEDED"
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_execute_raises_insufficient_stock():
    """Sin stock disponible → InsufficientStockException."""
    p_repo, b_repo, d_repo, l_repo, _ = _mock_repos(
        batches=[],
        monthly_used=0,
        limit=None,
    )

    with pytest.raises(InsufficientStockException):
        await execute_dispatch(
            fk_prescription_id=_PRESCRIPTION_ID,
            fk_pharmacist_id="pharmacist-001",
            patient_type="all",
            notes=None,
            pharmacist_id="pharmacist-001",
            prescription_repo=p_repo,
            batch_repo=b_repo,
            dispatch_repo=d_repo,
            limit_repo=l_repo,
        )


@pytest.mark.asyncio
async def test_execute_prescription_not_found():
    """Receta inexistente → NotFoundException."""
    p_repo, b_repo, d_repo, l_repo, _ = _mock_repos()
    p_repo.find_by_id.return_value = None

    with pytest.raises(NotFoundException):
        await execute_dispatch(
            fk_prescription_id="nonexistent",
            fk_pharmacist_id="pharmacist-001",
            patient_type="all",
            notes=None,
            pharmacist_id="pharmacist-001",
            prescription_repo=p_repo,
            batch_repo=b_repo,
            dispatch_repo=d_repo,
            limit_repo=l_repo,
        )
