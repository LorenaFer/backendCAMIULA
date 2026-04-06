"""Pydantic schemas for Inventory Reports."""

from typing import List, Optional

from pydantic import BaseModel, Field


# ── Medication embedded ──────────────────────────────────────────────────────

class MedicationOptionResponse(BaseModel):
    """Medication details embedded in report items."""

    id: str = Field(description="Medication UUID")
    code: str = Field(description="Medication code", example="MED-001")
    generic_name: str = Field(description="Generic name", example="Amoxicilina")
    pharmaceutical_form: str = Field(description="Form", example="tablet")
    unit_measure: str = Field(description="Unit", example="unit")
    current_stock: int = Field(description="Current available units", example=350)


# ── Stock report ─────────────────────────────────────────────────────────────

class StockItemResponse(BaseModel):
    """Single medication stock status."""

    medication_id: str = Field(description="Medication UUID")
    code: str = Field(description="Medication code", example="MED-001")
    generic_name: str = Field(description="Generic name", example="Amoxicilina")
    pharmaceutical_form: str = Field(description="Form", example="tablet")
    unit_measure: str = Field(description="Unit", example="unit")
    total_available: int = Field(description="Total available units across all active batches", example=350)
    batch_count: int = Field(description="Number of active batches", example=3)
    nearest_expiration: Optional[str] = Field(None, description="Nearest expiration date (ISO)", example="2026-08-15")
    days_to_expiration: Optional[int] = Field(None, description="Days until nearest batch expires", example=90)
    stock_alert: str = Field(description="Alert level: ok (>50), low (<=50), critical (<=10), expired (0)", example="ok")


class StockReportResponse(BaseModel):
    """Consolidated stock report across all medications."""

    generated_at: str = Field(description="Report generation timestamp (ISO)", example="2026-04-06T12:00:00+00:00")
    items: List[StockItemResponse] = Field(description="Stock status per medication")
    total_medications: int = Field(description="Total active medications in catalog", example=45)
    critical_count: int = Field(description="Medications with critical stock (<=10)", example=3)
    expired_count: int = Field(description="Medications with zero usable stock", example=1)


# ── KPIs ─────────────────────────────────────────────────────────────────────

class InventorySummaryResponse(BaseModel):
    """Executive inventory KPIs for the dashboard."""

    generated_at: str = Field(description="Timestamp", example="2026-04-06T12:00:00+00:00")
    total_active_skus: int = Field(description="Total active medications in catalog", example=45)
    critical_count: int = Field(description="Medications with critical stock", example=3)
    low_count: int = Field(description="Medications with low stock (<=50)", example=8)
    expired_count: int = Field(description="Medications with expired/zero stock", example=1)
    total_available_units: int = Field(description="Sum of all available units across all meds", example=12500)


# ── Expiration ───────────────────────────────────────────────────────────────

class EnrichedBatchResponse(BaseModel):
    """Batch with embedded medication details (for expiration reports)."""

    id: str = Field(description="Batch UUID")
    fk_medication_id: str = Field(description="Medication UUID")
    medication: MedicationOptionResponse = Field(description="Embedded medication details")
    fk_supplier_id: Optional[str] = Field(None, description="Supplier UUID")
    supplier_name: Optional[str] = Field(None, description="Supplier name")
    lot_number: str = Field(description="Lot number", example="LOT-2026-AMX-001")
    expiration_date: str = Field(description="Expiration date (ISO)", example="2026-08-15")
    quantity_received: int = Field(description="Original units", example=500)
    quantity_available: int = Field(description="Current available units", example=350)
    unit_cost: Optional[float] = Field(None, description="Unit cost", example=2.50)
    batch_status: str = Field(description="Status: available, depleted, expired", example="available")
    received_at: str = Field(description="Reception date", example="2026-04-01")


class ExpirationReportResponse(BaseModel):
    """Batches expiring within a threshold."""

    generated_at: str = Field(description="Timestamp")
    threshold_days: int = Field(description="Expiration horizon in days", example=90)
    batches: List[EnrichedBatchResponse] = Field(description="Batches expiring within threshold")


# ── Consumption ──────────────────────────────────────────────────────────────

class ConsumptionItemResponse(BaseModel):
    """Monthly consumption data for a medication."""

    medication_id: str = Field(description="Medication UUID")
    generic_name: str = Field(description="Medication name", example="Amoxicilina")
    total_dispatched: int = Field(description="Total units dispatched in the period", example=120)
    dispatch_count: int = Field(description="Number of distinct dispatches", example=15)
    patient_count: int = Field(description="Distinct patients served", example=12)


class ConsumptionReportResponse(BaseModel):
    """Monthly consumption report."""

    period: str = Field(description="Period in YYYY-MM format", example="2026-03")
    items: List[ConsumptionItemResponse] = Field(description="Consumption per medication")


# ── Kardex / Movements ───────────────────────────────────────────────────────

class MovementItemResponse(BaseModel):
    """A single kardex entry (batch received or item dispatched)."""

    movement_date: str = Field(description="Movement timestamp (ISO)", example="2026-04-01T10:30:00+00:00")
    movement_type: str = Field(description="Type: entry (batch) or exit (dispatch)", example="entry")
    reference: str = Field(description="Reference: PO number or prescription number", example="OC-2026-0001")
    lot_number: Optional[str] = Field(None, description="Batch lot number", example="LOT-2026-AMX-001")
    quantity: int = Field(description="Units moved", example=500)
    unit_cost: Optional[float] = Field(None, description="Unit cost at movement time", example=2.50)
    notes: Optional[str] = Field(None, description="Movement notes")


class PaginationMeta(BaseModel):
    """Pagination metadata."""

    total: int = Field(description="Total records", example=25)
    page: int = Field(description="Current page", example=1)
    page_size: int = Field(description="Items per page", example=20)
    pages: int = Field(description="Total pages", example=2)


class MovementsReportResponse(BaseModel):
    """Paginated kardex for a medication."""

    medication_id: str = Field(description="Medication UUID")
    generic_name: str = Field(description="Medication name", example="Amoxicilina")
    items: List[MovementItemResponse] = Field(description="Chronological movements")
    pagination: PaginationMeta = Field(description="Pagination info")


# ── Low-stock ────────────────────────────────────────────────────────────────

class LowStockReportResponse(BaseModel):
    """Medications with stock below threshold."""

    generated_at: str = Field(description="Timestamp")
    items: List[StockItemResponse] = Field(description="Medications with low/critical/expired stock")
    total: int = Field(description="Total medications with alerts", example=12)


# ── Expiring-soon (30/60/90 horizons) ───────────────────────────────────────

class ExpiringSoonReportResponse(BaseModel):
    """Batches grouped by expiration horizon."""

    generated_at: str = Field(description="Timestamp")
    vencen_en_30: List[EnrichedBatchResponse] = Field(description="Batches expiring in <= 30 days")
    vencen_en_60: List[EnrichedBatchResponse] = Field(description="Batches expiring in 31-60 days")
    vencen_en_90: List[EnrichedBatchResponse] = Field(description="Batches expiring in 61-90 days")
    total: int = Field(description="Total batches across all horizons", example=8)


# ── Inventory Movements (persisted) ─────────────────────────────────────────

class InventoryMovementResponse(BaseModel):
    """Persisted inventory movement record (traceability)."""

    id: str = Field(description="Movement UUID")
    fk_medication_id: str = Field(description="Medication UUID")
    medication_name: Optional[str] = Field(None, description="Medication name", example="Amoxicilina")
    fk_batch_id: Optional[str] = Field(None, description="Source batch UUID")
    fk_dispatch_id: Optional[str] = Field(None, description="Related dispatch UUID")
    fk_purchase_order_id: Optional[str] = Field(None, description="Related PO UUID")
    movement_type: str = Field(description="Type: entry, exit, adjustment, expiration", example="entry")
    quantity: int = Field(description="Units (positive=in, negative=out)", example=500)
    balance_after: int = Field(description="Stock balance after this movement", example=850)
    reference: Optional[str] = Field(None, description="Source reference", example="OC OC-2026-0001")
    lot_number: Optional[str] = Field(None, description="Lot number", example="LOT-2026-AMX-001")
    unit_cost: Optional[float] = Field(None, description="Unit cost", example=2.50)
    notes: Optional[str] = Field(None, description="Notes")
    movement_date: str = Field(description="Movement timestamp", example="2026-04-01T10:30:00+00:00")
    created_at: Optional[str] = Field(None, description="Record creation timestamp")
    created_by: Optional[str] = Field(None, description="Creator UUID")


class InventoryMovementsListResponse(BaseModel):
    """Paginated inventory movements."""

    items: List[InventoryMovementResponse] = Field(description="Movement records")
    pagination: PaginationMeta = Field(description="Pagination info")


# ── Stock Alerts ─────────────────────────────────────────────────────────────

class StockAlertResponse(BaseModel):
    """Persisted stock alert."""

    id: str = Field(description="Alert UUID")
    fk_medication_id: str = Field(description="Medication UUID")
    medication_name: Optional[str] = Field(None, description="Medication name", example="Ibuprofeno")
    medication_code: Optional[str] = Field(None, description="Medication code", example="MED-002")
    alert_level: str = Field(description="Severity: low, critical, expired", example="critical")
    current_stock: int = Field(description="Stock at time of alert", example=7)
    threshold: int = Field(description="Threshold that was crossed", example=10)
    message: str = Field(description="Alert message", example="Ibuprofeno: stock critico (7 <= 10 unidades)")
    detected_at: str = Field(description="When the alert was detected", example="2026-04-05T17:00:00+00:00")
    resolved_at: Optional[str] = Field(None, description="When the alert was resolved (null if active)")
    resolved_by: Optional[str] = Field(None, description="UUID of user who resolved it")
    alert_status: str = Field(description="Status: active, acknowledged, resolved", example="active")


class StockAlertsListResponse(BaseModel):
    """Stock alerts with counts."""

    items: List[StockAlertResponse] = Field(description="Alert records")
    total: int = Field(description="Total alerts matching filter", example=18)
    active_count: int = Field(description="Currently active alerts", example=11)
    resolved_count: int = Field(description="Resolved alerts", example=7)
