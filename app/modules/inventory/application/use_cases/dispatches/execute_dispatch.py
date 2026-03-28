"""Caso de uso: Ejecutar un despacho de farmacia (transacción atómica FEFO).

Flujo:
1. Validar receta (existe, no dispensada/cancelada).
2. Para cada ítem pendiente:
   a. Obtener lotes FEFO con SELECT FOR UPDATE (serialización concurrente).
   b. Verificar límite mensual → ForbiddenException si excedido sin excepción.
   c. Asignar unidades lote a lote en orden FEFO.
3. Crear registros Dispatch + DispatchItem.
4. Actualizar quantity_available de cada lote afectado.
5. Actualizar quantity_dispatched e item_status de cada PrescriptionItem.
6. Recalcular y actualizar prescription_status.
"""

from datetime import date, datetime, timezone
from typing import Optional

from app.core.exceptions import ForbiddenException, InsufficientStockException, NotFoundException
from app.modules.inventory.domain.entities.dispatch import Dispatch
from app.modules.inventory.domain.repositories.batch_repository import BatchRepository
from app.modules.inventory.domain.repositories.dispatch_repository import DispatchRepository
from app.modules.inventory.domain.repositories.limit_repository import LimitRepository
from app.modules.inventory.domain.repositories.prescription_repository import (
    PrescriptionRepository,
)

# Tipos internos para el plan de asignación por ítem
_BatchAllocation = list[tuple[str, int]]  # [(batch_id, qty_to_take), ...]


async def execute_dispatch(
    fk_prescription_id: str,
    fk_pharmacist_id: str,
    patient_type: str,
    notes: Optional[str],
    pharmacist_id: str,
    prescription_repo: PrescriptionRepository,
    batch_repo: BatchRepository,
    dispatch_repo: DispatchRepository,
    limit_repo: LimitRepository,
) -> Dispatch:
    # ── 1. Cargar y validar receta ────────────────────────────────────────────
    prescription = await prescription_repo.find_by_id(fk_prescription_id)
    if not prescription:
        raise NotFoundException("Receta no encontrada")

    if prescription.prescription_status in ("dispensed", "cancelled"):
        raise ForbiddenException(
            f"La receta está en estado '{prescription.prescription_status}'",
            code="INVALID_STATUS",
        )

    today = date.today()
    month = str(today.month)
    year = today.year
    reference_date = today.isoformat()

    # ── 2. Planificar asignaciones FEFO por ítem ──────────────────────────────
    item_allocations: list[dict] = []  # lista de dicts para crear DispatchItems

    for item in prescription.items:
        if item.item_status in ("dispensed", "cancelled"):
            continue

        remaining = item.quantity_prescribed - item.quantity_dispatched
        if remaining <= 0:
            continue

        # Lotes con SELECT FOR UPDATE — serializa concurrencia
        batches = await batch_repo.find_available_fefo(item.fk_medication_id)
        total_available = sum(b.quantity_available for b in batches)

        if total_available < remaining:
            raise InsufficientStockException(
                f"Stock insuficiente para '{item.fk_medication_id}': "
                f"disponible {total_available}, requerido {remaining}"
            )

        # ── Verificar límite mensual ──────────────────────────────────────────
        monthly_used = await dispatch_repo.get_monthly_consumption(
            fk_patient_id=prescription.fk_patient_id,
            fk_medication_id=item.fk_medication_id,
            month=month,
            year=year,
        )

        limit = await limit_repo.find_active_limit(
            fk_medication_id=item.fk_medication_id,
            applies_to=patient_type,
        )

        if limit and (monthly_used + remaining) > limit.monthly_max_quantity:
            exception = await limit_repo.find_active_exception(
                fk_patient_id=prescription.fk_patient_id,
                fk_medication_id=item.fk_medication_id,
                reference_date=reference_date,
            )
            if not exception or (monthly_used + remaining) > exception.authorized_quantity:
                effective_limit = (
                    exception.authorized_quantity if exception else limit.monthly_max_quantity
                )
                raise ForbiddenException(
                    f"Límite mensual excedido para el medicamento: "
                    f"{monthly_used} usados + {remaining} solicitados "
                    f"> {effective_limit} permitidos",
                    code="LIMIT_EXCEEDED",
                )

        # ── Asignar lotes FEFO ────────────────────────────────────────────────
        to_dispatch = remaining
        allocations: _BatchAllocation = []
        for batch in batches:
            if to_dispatch <= 0:
                break
            take = min(batch.quantity_available, to_dispatch)
            allocations.append((batch.id, take))
            to_dispatch -= take

        item_allocations.append(
            {
                "prescription_item_id": item.id,
                "fk_medication_id": item.fk_medication_id,
                "quantity_prescribed": item.quantity_prescribed,
                "quantity_dispatched_before": item.quantity_dispatched,
                "quantity_to_dispatch": remaining,
                "batch_allocations": allocations,
            }
        )

    if not item_allocations:
        raise ForbiddenException(
            "No hay ítems pendientes de despacho en esta receta",
            code="NOTHING_TO_DISPATCH",
        )

    # ── 3. Crear registro Dispatch + DispatchItems ────────────────────────────
    dispatch_items_data: list[dict] = []
    for alloc in item_allocations:
        for batch_id, qty in alloc["batch_allocations"]:
            dispatch_items_data.append(
                {
                    "fk_batch_id": batch_id,
                    "fk_medication_id": alloc["fk_medication_id"],
                    "quantity_dispatched": qty,
                }
            )

    dispatch = await dispatch_repo.create(
        data={
            "fk_prescription_id": fk_prescription_id,
            "fk_patient_id": prescription.fk_patient_id,
            "fk_pharmacist_id": fk_pharmacist_id,
            "dispatch_date": datetime.now(timezone.utc),
            "dispatch_status": "completed",
            "notes": notes,
            "items": dispatch_items_data,
        },
        created_by=pharmacist_id,
    )

    # ── 4. Actualizar cantidades en lotes ─────────────────────────────────────
    for alloc in item_allocations:
        for batch_id, qty in alloc["batch_allocations"]:
            # Releer lote para obtener cantidad actual post-flush
            batch = await batch_repo.find_by_id(batch_id)
            new_qty = batch.quantity_available - qty
            await batch_repo.update_quantity(batch_id, new_qty, pharmacist_id)

    # ── 5. Actualizar PrescriptionItems ───────────────────────────────────────
    for alloc in item_allocations:
        new_dispatched = alloc["quantity_dispatched_before"] + alloc["quantity_to_dispatch"]
        await prescription_repo.update_item_dispatched(
            item_id=alloc["prescription_item_id"],
            new_dispatched=new_dispatched,
            prescribed=alloc["quantity_prescribed"],
            updated_by=pharmacist_id,
        )

    # ── 6. Recalcular estado de la receta ─────────────────────────────────────
    # Recargar receta para ver los ítems actualizados
    updated_prescription = await prescription_repo.find_by_id(fk_prescription_id)
    active_items = [
        i for i in updated_prescription.items if i.item_status != "cancelled"
    ]
    all_dispensed = all(i.item_status == "dispensed" for i in active_items)
    any_partial = any(i.item_status in ("dispensed", "partial") for i in active_items)

    if all_dispensed:
        new_prescription_status = "dispensed"
    elif any_partial:
        new_prescription_status = "partial"
    else:
        new_prescription_status = "active"

    await prescription_repo.update_status(
        id=fk_prescription_id,
        new_status=new_prescription_status,
        updated_by=pharmacist_id,
    )

    return dispatch
