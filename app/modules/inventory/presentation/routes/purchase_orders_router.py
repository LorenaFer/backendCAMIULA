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
from app.modules.inventory.presentation.dependencies import (
    get_batch_repo, get_medication_repo, get_movement_repo, get_purchase_order_repo,
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
    """List purchase orders with supplier info and item details. Ordered by creation date descending."""
    repo = get_purchase_order_repo(session)
    items, total = await repo.find_all(page, page_size)
    data = [PurchaseOrderResponse(**o.__dict__) for o in items]
    return paginated(data, total, page, page_size, "Purchase orders retrieved")


@router.get("/{order_id}", summary="Get purchase order detail")
async def get_purchase_order(
    order_id: str,
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_optional_user_id),
):
    """Retrieve a purchase order with items, supplier details, and traceability fields."""
    repo = get_purchase_order_repo(session)
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
    """Create a purchase order in draft status. order_number is auto-generated."""
    repo = get_purchase_order_repo(session)
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
    """Transition a purchase order from draft to sent. Records sent_at and sent_by."""
    repo = get_purchase_order_repo(session)
    order = await repo.find_by_id(order_id)
    if not order:
        raise NotFoundException("Purchase order not found.")
    if order.order_status != "draft":
        raise AppException(
            f"Cannot send order in status '{order.order_status}'. Must be 'draft'.",
            status_code=400,
        )
    from datetime import datetime, timezone
    await repo.update_order_status(
        order_id, "sent", updated_by=user_id,
        sent_at=datetime.now(timezone.utc), sent_by=user_id,
    )
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
    """Register received items, creating batch records. Records inventory entry movements for traceability."""
    order_repo = get_purchase_order_repo(session)
    batch_repo = get_batch_repo(session)
    medication_repo = get_medication_repo(session)

    dto = ReceivePurchaseOrderDTO(
        order_id=order_id,
        items=[ReceivedItemDTO(**item.model_dump()) for item in body.items],
    )

    await ReceivePurchaseOrder(order_repo, batch_repo, medication_repo).execute(
        dto, received_by=user_id
    )

    # Record entry movements for traceability
    from datetime import datetime, timezone
    movement_repo = get_movement_repo(session)
    for item in body.items:
        # Resolve medication_id from the purchase order item
        po_item_row = await order_repo.find_item_by_id(item.purchase_order_item_id)
        if po_item_row:
            med_id = po_item_row.fk_medication_id
            balance = await movement_repo.get_current_balance(med_id)
            await movement_repo.record_movement(
                fk_medication_id=med_id,
                movement_type="entry",
                quantity=item.quantity_received,
                balance_after=balance,
                movement_date=datetime.now(timezone.utc),
                created_by=user_id,
                fk_purchase_order_id=order_id,
                reference=f"PO receive {order_id[:8]}",
                lot_number=item.lot_number,
                unit_cost=item.unit_cost,
            )

    return ok(message="Reception registered successfully.")
