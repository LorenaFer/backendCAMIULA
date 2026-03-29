"""Caso de uso: Validar y preparar un despacho (FEFO + límites mensuales).

Retorna un DispatchValidationDTO con el análisis por ítem.
No ejecuta ninguna escritura — es una operación de solo lectura.
"""

from datetime import date
from typing import Optional

from app.core.exceptions import NotFoundException
from app.modules.inventory.application.dtos.dispatch_dto import (
    DispatchValidationDTO,
    DispatchValidationItemDTO,
)
from app.modules.inventory.domain.repositories.batch_repository import BatchRepository
from app.modules.inventory.domain.repositories.dispatch_repository import DispatchRepository
from app.modules.inventory.domain.repositories.limit_repository import LimitRepository
from app.modules.inventory.domain.repositories.medication_repository import MedicationRepository
from app.modules.inventory.domain.repositories.prescription_repository import (
    PrescriptionRepository,
)


async def validate_and_prepare_dispatch(
    prescription_id: str,
    patient_type: str,
    prescription_repo: PrescriptionRepository,
    batch_repo: BatchRepository,
    dispatch_repo: DispatchRepository,
    limit_repo: LimitRepository,
    medication_repo: MedicationRepository,
) -> DispatchValidationDTO:
    prescription = await prescription_repo.find_by_id(prescription_id)
    if not prescription:
        raise NotFoundException("Receta no encontrada")

    if prescription.prescription_status in ("dispensed", "cancelled"):
        raise NotFoundException(
            f"La receta está en estado '{prescription.prescription_status}'"
            " y no puede ser despachada"
        )

    today = date.today()
    month = str(today.month)
    year = today.year
    reference_date = today.isoformat()

    item_results: list[DispatchValidationItemDTO] = []
    overall_can_dispatch = True

    # Pre-load medication names for all pending items (avoids N+1 per item)
    pending_med_ids = {
        item.fk_medication_id
        for item in prescription.items
        if item.item_status not in ("dispensed", "cancelled")
        and item.quantity_prescribed - item.quantity_dispatched > 0
    }
    med_names: dict[str, str] = {}
    for med_id in pending_med_ids:
        medication = await medication_repo.find_by_id(med_id)
        med_names[med_id] = medication.generic_name if medication else med_id

    for item in prescription.items:
        if item.item_status in ("dispensed", "cancelled"):
            continue

        remaining = item.quantity_prescribed - item.quantity_dispatched
        if remaining <= 0:
            continue

        # Stock disponible en orden FEFO (solo lectura, sin SELECT FOR UPDATE aquí)
        batches = await batch_repo.find_available_fefo(item.fk_medication_id)
        total_available = sum(b.quantity_available for b in batches)

        # Consumo mensual acumulado
        monthly_used = await dispatch_repo.get_monthly_consumption(
            fk_patient_id=prescription.fk_patient_id,
            fk_medication_id=item.fk_medication_id,
            month=month,
            year=year,
        )

        # Límite mensual activo (específico para el tipo de beneficiario o "all")
        limit = await limit_repo.find_active_limit(
            fk_medication_id=item.fk_medication_id,
            applies_to=patient_type,
        )

        monthly_limit: Optional[int] = limit.monthly_max_quantity if limit else None
        monthly_remaining: Optional[int] = (
            monthly_limit - monthly_used if monthly_limit is not None else None
        )

        has_exception = False
        can_dispatch = True
        block_reason: Optional[str] = None

        if total_available < remaining:
            can_dispatch = False
            block_reason = (
                f"Stock insuficiente: disponible {total_available}, "
                f"requerido {remaining}"
            )
        elif monthly_limit is not None and (monthly_used + remaining) > monthly_limit:
            exception = await limit_repo.find_active_exception(
                fk_patient_id=prescription.fk_patient_id,
                fk_medication_id=item.fk_medication_id,
                reference_date=reference_date,
            )
            if exception:
                has_exception = True
                if monthly_used + remaining > exception.authorized_quantity:
                    can_dispatch = False
                    block_reason = (
                        f"Excede la cantidad autorizada por excepción: "
                        f"{monthly_used} usados + {remaining} solicitados "
                        f"> {exception.authorized_quantity} autorizados"
                    )
            else:
                can_dispatch = False
                block_reason = (
                    f"Límite mensual excedido: {monthly_used} usados + "
                    f"{remaining} solicitados > {monthly_limit} permitidos"
                )

        if not can_dispatch:
            overall_can_dispatch = False

        generic_name = med_names.get(item.fk_medication_id, item.fk_medication_id)

        item_results.append(
            DispatchValidationItemDTO(
                medication_id=item.fk_medication_id,
                generic_name=generic_name,
                quantity_prescribed=item.quantity_prescribed,
                quantity_available=total_available,
                monthly_limit=monthly_limit,
                monthly_used=monthly_used,
                monthly_remaining=monthly_remaining,
                has_exception=has_exception,
                can_dispatch=can_dispatch,
                block_reason=block_reason,
            )
        )

    return DispatchValidationDTO(
        can_dispatch=overall_can_dispatch,
        prescription_id=prescription.id,
        patient_id=prescription.fk_patient_id,
        items=item_results,
    )
