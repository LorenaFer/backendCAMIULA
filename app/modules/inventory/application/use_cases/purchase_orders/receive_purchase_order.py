"""Caso de uso: Recibir una orden de compra.

Registra los lotes recibidos, actualiza el stock del catálogo de medicamentos
de forma atómica y cierra la orden. Todo el proceso corre dentro de la
transacción de la sesión de SQLAlchemy provista por el caller.

Autor: Julio Vasquez
"""

from datetime import date

from app.core.exceptions import ForbiddenException, NotFoundException
from app.modules.inventory.application.dtos.purchase_order_dto import (
    ReceivePurchaseOrderDTO,
)
from app.modules.inventory.domain.repositories.batch_repository import BatchRepository
from app.modules.inventory.domain.repositories.medication_repository import (
    MedicationRepository,
)
from app.modules.inventory.domain.repositories.purchase_order_repository import (
    PurchaseOrderRepository,
)

# Estados de orden que permiten registrar una recepción
_RECEIVABLE_STATUSES: frozenset[str] = frozenset({"sent", "partial"})


class ReceivePurchaseOrder:
    """Registra la recepción física de una orden de compra.

    Por cada ítem recibido:
      1. Valida que el ítem y su medicamento existan en el catálogo.
      2. Crea un nuevo lote (Batch) vinculado al medicamento existente —
         esto incrementa automáticamente el stock calculado del catálogo
         sin crear duplicados en la tabla medications.
      3. Acumula quantity_received en el ítem de la orden mediante una
         operación DB-side (quantity_received + delta) para tolerar
         recepciones parciales concurrentes sin condiciones de carrera.

    Al finalizar todos los ítems, la orden pasa al estado "received".
    """

    def __init__(
        self,
        order_repo: PurchaseOrderRepository,
        batch_repo: BatchRepository,
        medication_repo: MedicationRepository,
    ) -> None:
        self._order_repo = order_repo
        self._batch_repo = batch_repo
        self._medication_repo = medication_repo

    async def execute(
        self, dto: ReceivePurchaseOrderDTO, received_by: str
    ) -> None:
        # ── 1. Validar que la orden existe y su estado es receptible ──────
        order = await self._order_repo.find_by_id(dto.order_id)
        if not order:
            raise NotFoundException("Orden de compra no encontrada.")

        if order.order_status not in _RECEIVABLE_STATUSES:
            raise ForbiddenException(
                f"La orden '{order.order_number}' no puede recibirse en su "
                f"estado actual: '{order.order_status}'.",
                code="INVALID_ORDER_STATUS",
            )

        today = date.today()

        # ── 2. Procesar cada ítem recibido ────────────────────────────────
        for received_item in dto.items:

            # Validación de negocio: cantidad positiva obligatoria
            if received_item.quantity_received <= 0:
                raise ForbiddenException(
                    "La cantidad recibida debe ser mayor a cero.",
                    code="INVALID_QUANTITY",
                )

            # Buscar el ítem de la orden
            po_item = await self._order_repo.find_item_by_id(
                received_item.purchase_order_item_id
            )
            if not po_item:
                raise NotFoundException(
                    f"Ítem de orden '{received_item.purchase_order_item_id}' no encontrado."
                )

            # Verificar que el medicamento existe en el catálogo
            medication = await self._medication_repo.find_by_id(
                po_item.fk_medication_id
            )
            if not medication:
                raise NotFoundException(
                    f"Medicamento con ID '{po_item.fk_medication_id}' no "
                    "encontrado en el catálogo."
                )

            # Crear nuevo lote vinculado al medicamento existente.
            # quantity_available = quantity_received: el lote entra disponible
            # en su totalidad; el stock del catálogo se recalcula desde los
            # lotes activos, por lo que esto constituye el incremento de stock.
            await self._batch_repo.create(
                data={
                    "fk_medication_id": po_item.fk_medication_id,
                    "fk_supplier_id": order.fk_supplier_id,
                    "fk_purchase_order_id": order.id,
                    "lot_number": received_item.lot_number,
                    "expiration_date": received_item.expiration_date,
                    "quantity_received": received_item.quantity_received,
                    "quantity_available": received_item.quantity_received,
                    "received_at": today,
                    "batch_status": "available",
                    "unit_cost": received_item.unit_cost,
                },
                created_by=received_by,
            )

            # Acumular quantity_received en el ítem con operación DB-side
            new_total = po_item.quantity_received + received_item.quantity_received
            item_status = (
                "received" if new_total >= po_item.quantity_ordered else "partial"
            )
            await self._order_repo.increment_item_received(
                item_id=po_item.id,
                quantity_delta=received_item.quantity_received,
                item_status=item_status,
                unit_cost=received_item.unit_cost,
                updated_by=received_by,
            )

        # ── 3. Cerrar la orden ────────────────────────────────────────────
        await self._order_repo.update_order_status(
            id=dto.order_id,
            status="received",
            updated_by=received_by,
        )
