"""Rutas FastAPI para el recurso Orden de Compra."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenException, NotFoundException
from app.modules.inventory.application.dtos.purchase_order_dto import (
    ReceivedItemDTO,
    ReceivePurchaseOrderDTO,
)
from app.modules.inventory.application.use_cases.purchase_orders.receive_purchase_order import (
    ReceivePurchaseOrder,
)
from app.modules.inventory.infrastructure.repositories.sqlalchemy_batch_repository import (
    SQLAlchemyBatchRepository,
)
from app.modules.inventory.infrastructure.repositories.sqlalchemy_medication_repository import (
    SQLAlchemyMedicationRepository,
)
from app.modules.inventory.infrastructure.repositories.sqlalchemy_purchase_order_repository import (
    SQLAlchemyPurchaseOrderRepository,
)
from app.modules.inventory.presentation.schemas.purchase_order_schemas import (
    ReceiveItemInput,
    ReceivePurchaseOrderInput,
)
from app.shared.database.session import get_db
from app.shared.middleware.auth import get_current_user_id
from app.shared.schemas.responses import ok

router = APIRouter(prefix="/purchase-orders", tags=["Inventory — Purchase Orders"])


@router.post(
    "/{order_id}/receive",
    summary="Registrar recepción de una orden de compra",
    status_code=200,
)
async def receive_purchase_order(
    order_id: str,
    body: ReceivePurchaseOrderInput,
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Registra los lotes recibidos, actualiza el stock del catálogo y
    cierra la orden. Todo el proceso es atómico dentro de una transacción.

    - **order_id**: UUID de la orden de compra a recibir.
    - **items**: Lista de ítems con lote, vencimiento y cantidad recibida.
    """
    order_repo = SQLAlchemyPurchaseOrderRepository(session)
    batch_repo = SQLAlchemyBatchRepository(session)
    medication_repo = SQLAlchemyMedicationRepository(session)

    dto = ReceivePurchaseOrderDTO(
        order_id=order_id,
        items=[
            ReceivedItemDTO(
                purchase_order_item_id=item.purchase_order_item_id,
                quantity_received=item.quantity_received,
                lot_number=item.lot_number,
                expiration_date=item.expiration_date,
                unit_cost=item.unit_cost,
            )
            for item in body.items
        ],
    )

    await ReceivePurchaseOrder(order_repo, batch_repo, medication_repo).execute(
        dto, received_by=user_id
    )

    return ok(message="Recepción registrada exitosamente.")
