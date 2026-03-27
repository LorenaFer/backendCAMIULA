"""Caso de uso: Cancelar un despacho y revertir el stock.

Flujo:
1. Cargar el despacho → error si no existe o ya está cancelado.
2. Para cada DispatchItem, restaurar quantity_available en el lote correspondiente.
3. Marcar el despacho como 'cancelled'.
4. Recalcular item_status y prescription_status de la receta asociada.
"""

from app.core.exceptions import ForbiddenException, NotFoundException
from app.modules.inventory.domain.repositories.batch_repository import BatchRepository
from app.modules.inventory.domain.repositories.dispatch_repository import DispatchRepository
from app.modules.inventory.domain.repositories.prescription_repository import (
    PrescriptionRepository,
)


async def cancel_dispatch(
    dispatch_id: str,
    cancelled_by: str,
    dispatch_repo: DispatchRepository,
    batch_repo: BatchRepository,
    prescription_repo: PrescriptionRepository,
) -> None:
    # ── 1. Cargar despacho ────────────────────────────────────────────────────
    dispatch = await dispatch_repo.find_by_id(dispatch_id)
    if not dispatch:
        raise NotFoundException("Despacho no encontrado")

    if dispatch.dispatch_status == "cancelled":
        raise ForbiddenException(
            "El despacho ya está cancelado",
            code="ALREADY_CANCELLED",
        )

    # ── 2. Revertir stock en lotes ────────────────────────────────────────────
    for item in dispatch.items:
        batch = await batch_repo.find_by_id(item.fk_batch_id)
        if batch:
            restored_qty = batch.quantity_available + item.quantity_dispatched
            await batch_repo.update_quantity(item.fk_batch_id, restored_qty, cancelled_by)

    # ── 3. Cancelar despacho ──────────────────────────────────────────────────
    await dispatch_repo.update_status(dispatch_id, "cancelled", cancelled_by)

    # ── 4. Recalcular estado de la receta ─────────────────────────────────────
    prescription = await prescription_repo.find_by_id(dispatch.fk_prescription_id)
    if not prescription:
        return  # La receta ya no existe (soft-deleted); no actualizar

    # Revertir quantity_dispatched por medication agrupando ítems del despacho
    # Mapa: medication_id → qty a restar
    qty_to_revert: dict[str, int] = {}
    for d_item in dispatch.items:
        qty_to_revert[d_item.fk_medication_id] = (
            qty_to_revert.get(d_item.fk_medication_id, 0) + d_item.quantity_dispatched
        )

    for p_item in prescription.items:
        if p_item.item_status == "cancelled":
            continue
        revert = qty_to_revert.get(p_item.fk_medication_id, 0)
        if revert == 0:
            continue
        new_dispatched = max(0, p_item.quantity_dispatched - revert)
        await prescription_repo.update_item_dispatched(
            item_id=p_item.id,
            new_dispatched=new_dispatched,
            prescribed=p_item.quantity_prescribed,
            updated_by=cancelled_by,
        )

    # Recalcular estado global de la receta
    updated_prescription = await prescription_repo.find_by_id(dispatch.fk_prescription_id)
    active_items = [
        i for i in updated_prescription.items if i.item_status != "cancelled"
    ]

    if not active_items:
        new_status = "cancelled"
    elif all(i.quantity_dispatched == 0 for i in active_items):
        new_status = "active"
    elif all(i.item_status == "dispensed" for i in active_items):
        new_status = "dispensed"
    else:
        new_status = "partial"

    await prescription_repo.update_status(
        id=dispatch.fk_prescription_id,
        new_status=new_status,
        updated_by=cancelled_by,
    )
