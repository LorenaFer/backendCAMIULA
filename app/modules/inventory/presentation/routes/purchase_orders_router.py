"""FastAPI routes for Purchase Orders."""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException, NotFoundException
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
    PurchaseOrderCreate,
    PurchaseOrderResponse,
    ReceivePurchaseOrderInput,
)
from app.shared.database.session import get_db
from app.shared.middleware.auth import get_current_user_id, get_optional_user_id
from app.shared.schemas.responses import created, ok, paginated

router = APIRouter(prefix="/purchase-orders", tags=["Inventory — Purchase Orders"])


@router.get("", summary="List purchase orders (paginated)")
async def list_purchase_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=10000),
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_optional_user_id),
):
    repo = SQLAlchemyPurchaseOrderRepository(session)
    items, total = await repo.find_all(page, page_size)
    data = [PurchaseOrderResponse(**o.__dict__) for o in items]
    return paginated(data, total, page, page_size, "Purchase orders retrieved")


@router.get("/{order_id}", summary="Get purchase order detail")
async def get_purchase_order(
    order_id: str,
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_optional_user_id),
):
    repo = SQLAlchemyPurchaseOrderRepository(session)
    order = await repo.find_by_id(order_id)
    if not order:
        raise NotFoundException("Purchase order not found.")
    return ok(data=PurchaseOrderResponse(**order.__dict__), message="Order retrieved")


@router.post("", summary="Create purchase order", status_code=201)
async def create_purchase_order(
    body: PurchaseOrderCreate,
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    repo = SQLAlchemyPurchaseOrderRepository(session)
    order_number = await repo.get_next_order_number()

    data = body.model_dump()
    items_raw = data.pop("items", [])
    items = [
        {
            "medication_id": item["medication_id"],
            "quantity_ordered": item["quantity_ordered"],
            "unit_cost": item.get("unit_cost"),
        }
        for item in items_raw
    ]

    order = await repo.create(
        {
            "order_number": order_number,
            "order_date": date.today(),
            "order_status": "draft",
            "fk_supplier_id": data["fk_supplier_id"],
            "expected_date": data.get("expected_date"),
            "notes": data.get("notes"),
            "items": items,
        },
        created_by=user_id,
    )
    return created(
        data=PurchaseOrderResponse(**order.__dict__),
        message="Purchase order created successfully",
    )


@router.post("/{order_id}/send", summary="Send purchase order (draft → sent)")
async def send_purchase_order(
    order_id: str,
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    repo = SQLAlchemyPurchaseOrderRepository(session)
    order = await repo.find_by_id(order_id)
    if not order:
        raise NotFoundException("Purchase order not found.")
    if order.order_status != "draft":
        raise AppException(
            f"Cannot send order in status '{order.order_status}'. Must be 'draft'.",
            status_code=400,
        )
    await repo.update_order_status(order_id, "sent", updated_by=user_id)
    updated = await repo.find_by_id(order_id)
    return ok(data=PurchaseOrderResponse(**updated.__dict__), message="Order sent")


@router.post(
    "/{order_id}/receive",
    summary="Receive purchase order (creates batches, updates stock)",
)
async def receive_purchase_order(
    order_id: str,
    body: ReceivePurchaseOrderInput,
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    order_repo = SQLAlchemyPurchaseOrderRepository(session)
    batch_repo = SQLAlchemyBatchRepository(session)
    medication_repo = SQLAlchemyMedicationRepository(session)

    dto = ReceivePurchaseOrderDTO(
        order_id=order_id,
        items=[ReceivedItemDTO(**item.model_dump()) for item in body.items],
    )

    await ReceivePurchaseOrder(order_repo, batch_repo, medication_repo).execute(
        dto, received_by=user_id
    )
    return ok(message="Reception registered successfully.")
