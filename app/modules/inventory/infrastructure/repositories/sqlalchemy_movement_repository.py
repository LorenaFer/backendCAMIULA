"""Repository for inventory movements and stock alerts.

Handles persisted movement records (entry/exit/adjustment/expiration)
and stock alerts (low/critical/expired) with full traceability.

Complexity:
    - record_movement: O(1) insert
    - get_movements: O(log N + k) with index on (fk_medication_id, movement_date)
    - generate_alerts: O(M) where M = active medications (runs once per stock report)
    - get_alerts: O(log N + k) with index on (alert_status, detected_at)
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlalchemy import and_, func, select, update as sql_update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.inventory.application.dtos.report_dto import (
    STOCK_THRESHOLD_CRITICAL,
    STOCK_THRESHOLD_LOW,
    InventoryMovementDTO,
    InventoryMovementsListDTO,
    StockAlertDTO,
    StockAlertsListDTO,
)
from app.modules.inventory.infrastructure.models import (
    BatchModel,
    InventoryMovementModel,
    MedicationModel,
    StockAlertModel,
)
from app.shared.database.mixins import RecordStatus


class SQLAlchemyMovementRepository:

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ──────────────────────────────────────────────────────────
    # Inventory Movements
    # ──────────────────────────────────────────────────────────

    async def record_movement(
        self,
        fk_medication_id: str,
        movement_type: str,
        quantity: int,
        balance_after: int,
        movement_date: datetime,
        created_by: str,
        fk_batch_id: Optional[str] = None,
        fk_dispatch_id: Optional[str] = None,
        fk_purchase_order_id: Optional[str] = None,
        reference: Optional[str] = None,
        lot_number: Optional[str] = None,
        unit_cost: Optional[float] = None,
        notes: Optional[str] = None,
    ) -> str:
        """Insert a single movement record. O(1).

        Returns the movement ID.
        """
        movement_id = str(uuid4())
        model = InventoryMovementModel(
            id=movement_id,
            fk_medication_id=fk_medication_id,
            fk_batch_id=fk_batch_id,
            fk_dispatch_id=fk_dispatch_id,
            fk_purchase_order_id=fk_purchase_order_id,
            movement_type=movement_type,
            quantity=quantity,
            balance_after=balance_after,
            reference=reference,
            lot_number=lot_number,
            unit_cost=unit_cost,
            notes=notes,
            movement_date=movement_date,
            created_by=created_by,
        )
        self._session.add(model)
        await self._session.flush()
        return movement_id

    async def get_current_balance(self, fk_medication_id: str) -> int:
        """Get current usable stock for a medication.

        Sums quantity_available from batches with status='available',
        expiration_date >= today, and record status = 'A'.
        O(log N) with index on fk_medication_id.
        """
        from datetime import date
        today = date.today()
        result = await self._session.execute(
            select(
                func.coalesce(func.sum(BatchModel.quantity_available), 0)
            ).where(
                BatchModel.fk_medication_id == fk_medication_id,
                BatchModel.status == RecordStatus.ACTIVE,
                BatchModel.batch_status == "available",
                BatchModel.expiration_date >= today,
                BatchModel.quantity_available > 0,
            )
        )
        return int(result.scalar_one())

    async def get_movements(
        self,
        medication_id: Optional[str] = None,
        movement_type: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> InventoryMovementsListDTO:
        """Paginated list of persisted movements with medication name.

        O(log N + k) with composite index on (fk_medication_id, movement_date).
        """
        q = (
            select(
                InventoryMovementModel,
                MedicationModel.generic_name.label("medication_name"),
            )
            .join(
                MedicationModel,
                MedicationModel.id == InventoryMovementModel.fk_medication_id,
            )
            .where(InventoryMovementModel.status == RecordStatus.ACTIVE)
        )

        if medication_id:
            q = q.where(InventoryMovementModel.fk_medication_id == medication_id)
        if movement_type:
            q = q.where(InventoryMovementModel.movement_type == movement_type)
        if date_from:
            q = q.where(
                InventoryMovementModel.movement_date >= datetime.fromisoformat(date_from)
            )
        if date_to:
            q = q.where(
                InventoryMovementModel.movement_date <= datetime.fromisoformat(date_to)
            )

        # Count
        count_q = select(func.count()).select_from(q.subquery())
        total = (await self._session.execute(count_q)).scalar_one()

        # Paginated
        offset = (page - 1) * page_size
        rows = (
            await self._session.execute(
                q.order_by(InventoryMovementModel.movement_date.desc())
                .offset(offset)
                .limit(page_size)
            )
        ).all()

        items = []
        for row in rows:
            m = row[0]
            med_name = row[1]
            items.append(
                InventoryMovementDTO(
                    id=m.id,
                    fk_medication_id=m.fk_medication_id,
                    medication_name=med_name,
                    fk_batch_id=m.fk_batch_id,
                    fk_dispatch_id=m.fk_dispatch_id,
                    fk_purchase_order_id=m.fk_purchase_order_id,
                    movement_type=m.movement_type,
                    quantity=m.quantity,
                    balance_after=m.balance_after,
                    reference=m.reference,
                    lot_number=m.lot_number,
                    unit_cost=float(m.unit_cost) if m.unit_cost else None,
                    notes=m.notes,
                    movement_date=m.movement_date.isoformat() if m.movement_date else "",
                    created_at=m.created_at.isoformat() if m.created_at else None,
                    created_by=m.created_by,
                )
            )

        return InventoryMovementsListDTO(items=items, total=total)

    # ──────────────────────────────────────────────────────────
    # Stock Alerts
    # ──────────────────────────────────────────────────────────

    async def generate_alerts(self, created_by: str = "system") -> int:
        """Scan all active medications, create alerts for those crossing thresholds.

        Only creates a new alert if there is no existing active alert for
        that medication at the same level. Auto-resolves alerts when stock
        recovers above threshold.

        Returns the number of new alerts created.
        O(M) where M = number of active medications.
        """
        from datetime import date
        today = date.today()
        now = datetime.now(timezone.utc)

        # Get current stock per medication
        stock_sq = (
            select(
                BatchModel.fk_medication_id,
                func.coalesce(func.sum(BatchModel.quantity_available), 0).label(
                    "total_available"
                ),
            )
            .where(
                BatchModel.status == RecordStatus.ACTIVE,
                BatchModel.batch_status == "available",
                BatchModel.expiration_date >= today,
                BatchModel.quantity_available > 0,
            )
            .group_by(BatchModel.fk_medication_id)
            .subquery()
        )

        rows = (
            await self._session.execute(
                select(
                    MedicationModel.id,
                    MedicationModel.generic_name,
                    MedicationModel.code,
                    func.coalesce(stock_sq.c.total_available, 0).label("stock"),
                )
                .outerjoin(stock_sq, stock_sq.c.fk_medication_id == MedicationModel.id)
                .where(
                    MedicationModel.status == RecordStatus.ACTIVE,
                    MedicationModel.medication_status == "active",
                )
            )
        ).all()

        # Get existing active alerts
        active_alerts_result = await self._session.execute(
            select(
                StockAlertModel.fk_medication_id,
                StockAlertModel.alert_level,
                StockAlertModel.id,
            ).where(
                StockAlertModel.status == RecordStatus.ACTIVE,
                StockAlertModel.alert_status == "active",
            )
        )
        active_alerts = {}
        for a in active_alerts_result.all():
            active_alerts[(a[0], a[1])] = a[2]

        new_count = 0
        for row in rows:
            med_id = row.id
            med_name = row.generic_name
            stock = int(row.stock)

            # Determine alert level
            if stock == 0:
                level = "expired"
                threshold = 0
                msg = f"{med_name}: stock agotado (0 unidades)"
            elif stock <= STOCK_THRESHOLD_CRITICAL:
                level = "critical"
                threshold = STOCK_THRESHOLD_CRITICAL
                msg = f"{med_name}: stock critico ({stock} <= {threshold} unidades)"
            elif stock <= STOCK_THRESHOLD_LOW:
                level = "low"
                threshold = STOCK_THRESHOLD_LOW
                msg = f"{med_name}: stock bajo ({stock} <= {threshold} unidades)"
            else:
                # Stock is OK — resolve any active alerts for this medication
                for alert_level in ("low", "critical", "expired"):
                    key = (med_id, alert_level)
                    if key in active_alerts:
                        await self._session.execute(
                            sql_update(StockAlertModel)
                            .where(StockAlertModel.id == active_alerts[key])
                            .values(
                                alert_status="resolved",
                                resolved_at=now,
                                resolved_by=created_by,
                                updated_at=now,
                                updated_by=created_by,
                            )
                        )
                continue

            # Check if alert already exists
            key = (med_id, level)
            if key not in active_alerts:
                alert = StockAlertModel(
                    id=str(uuid4()),
                    fk_medication_id=med_id,
                    alert_level=level,
                    current_stock=stock,
                    threshold=threshold,
                    message=msg,
                    detected_at=now,
                    alert_status="active",
                    created_by=created_by,
                )
                self._session.add(alert)
                new_count += 1

            # Resolve alerts of lower severity that no longer apply
            if level == "critical":
                low_key = (med_id, "low")
                if low_key in active_alerts:
                    await self._session.execute(
                        sql_update(StockAlertModel)
                        .where(StockAlertModel.id == active_alerts[low_key])
                        .values(
                            alert_status="resolved",
                            resolved_at=now,
                            resolved_by=created_by,
                            updated_at=now,
                            updated_by=created_by,
                        )
                    )
            elif level == "expired":
                for lower in ("low", "critical"):
                    lower_key = (med_id, lower)
                    if lower_key in active_alerts:
                        await self._session.execute(
                            sql_update(StockAlertModel)
                            .where(StockAlertModel.id == active_alerts[lower_key])
                            .values(
                                alert_status="resolved",
                                resolved_at=now,
                                resolved_by=created_by,
                                updated_at=now,
                                updated_by=created_by,
                            )
                        )

        await self._session.flush()
        return new_count

    async def get_alerts(
        self,
        alert_status: Optional[str] = None,
        alert_level: Optional[str] = None,
        medication_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> StockAlertsListDTO:
        """Paginated list of stock alerts with medication info.

        O(log N + k) with composite index on (alert_status, detected_at).
        """
        q = (
            select(
                StockAlertModel,
                MedicationModel.generic_name.label("medication_name"),
                MedicationModel.code.label("medication_code"),
            )
            .join(
                MedicationModel,
                MedicationModel.id == StockAlertModel.fk_medication_id,
            )
            .where(StockAlertModel.status == RecordStatus.ACTIVE)
        )

        if alert_status:
            q = q.where(StockAlertModel.alert_status == alert_status)
        if alert_level:
            q = q.where(StockAlertModel.alert_level == alert_level)
        if medication_id:
            q = q.where(StockAlertModel.fk_medication_id == medication_id)

        # Counts
        total = (
            await self._session.execute(
                select(func.count()).select_from(q.subquery())
            )
        ).scalar_one()

        active_count = (
            await self._session.execute(
                select(func.count()).where(
                    StockAlertModel.status == RecordStatus.ACTIVE,
                    StockAlertModel.alert_status == "active",
                )
            )
        ).scalar_one()

        resolved_count = (
            await self._session.execute(
                select(func.count()).where(
                    StockAlertModel.status == RecordStatus.ACTIVE,
                    StockAlertModel.alert_status == "resolved",
                )
            )
        ).scalar_one()

        # Paginated
        offset = (page - 1) * page_size
        rows = (
            await self._session.execute(
                q.order_by(StockAlertModel.detected_at.desc())
                .offset(offset)
                .limit(page_size)
            )
        ).all()

        items = []
        for row in rows:
            a = row[0]
            items.append(
                StockAlertDTO(
                    id=a.id,
                    fk_medication_id=a.fk_medication_id,
                    medication_name=row[1],
                    medication_code=row[2],
                    alert_level=a.alert_level,
                    current_stock=a.current_stock,
                    threshold=a.threshold,
                    message=a.message,
                    detected_at=a.detected_at.isoformat() if a.detected_at else "",
                    resolved_at=a.resolved_at.isoformat() if a.resolved_at else None,
                    resolved_by=a.resolved_by,
                    alert_status=a.alert_status,
                )
            )

        return StockAlertsListDTO(
            items=items,
            total=total,
            active_count=active_count,
            resolved_count=resolved_count,
        )

    async def acknowledge_alert(self, alert_id: str, user_id: str) -> bool:
        """Mark an alert as acknowledged. Returns False if not found."""
        now = datetime.now(timezone.utc)
        result = await self._session.execute(
            sql_update(StockAlertModel)
            .where(
                StockAlertModel.id == alert_id,
                StockAlertModel.status == RecordStatus.ACTIVE,
                StockAlertModel.alert_status == "active",
            )
            .values(
                alert_status="acknowledged",
                updated_at=now,
                updated_by=user_id,
            )
        )
        return result.rowcount > 0

    async def resolve_alert(self, alert_id: str, user_id: str) -> bool:
        """Manually resolve an alert. Returns False if not found."""
        now = datetime.now(timezone.utc)
        result = await self._session.execute(
            sql_update(StockAlertModel)
            .where(
                StockAlertModel.id == alert_id,
                StockAlertModel.status == RecordStatus.ACTIVE,
                StockAlertModel.alert_status.in_(["active", "acknowledged"]),
            )
            .values(
                alert_status="resolved",
                resolved_at=now,
                resolved_by=user_id,
                updated_at=now,
                updated_by=user_id,
            )
        )
        return result.rowcount > 0
