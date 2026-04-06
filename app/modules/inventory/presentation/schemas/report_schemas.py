"""Schemas Pydantic para los reportes de inventario.

Espejo 1:1 de las interfaces TypeScript definidas en inventory.ts:
  StockItem, StockReport, ConsumptionItem, ConsumptionReport,
  ExpirationReport (con Batch + MedicationOption embebido).
"""

from typing import List, Optional

from pydantic import BaseModel


# ── Medicamento embebido (MedicationOption TypeScript) ────────────────────────

class MedicationOptionResponse(BaseModel):
    id: str
    code: str
    generic_name: str
    pharmaceutical_form: str
    unit_measure: str
    current_stock: int


# ── Stock consolidado (StockItem TypeScript) ──────────────────────────────────

class StockItemResponse(BaseModel):
    """Espejo de la interfaz StockItem del frontend."""
    medication_id: str
    code: str
    generic_name: str
    pharmaceutical_form: str
    unit_measure: str
    total_available: int
    batch_count: int
    nearest_expiration: Optional[str] = None
    days_to_expiration: Optional[int] = None
    stock_alert: str  # 'ok' | 'low' | 'critical' | 'expired'


class StockReportResponse(BaseModel):
    """Espejo de la interfaz StockReport del frontend."""
    generated_at: str
    items: List[StockItemResponse]
    total_medications: int
    critical_count: int
    expired_count: int


# ── Resumen ejecutivo (KPIs del dashboard) ────────────────────────────────────

class InventorySummaryResponse(BaseModel):
    generated_at: str
    total_active_skus: int
    critical_count: int
    low_count: int
    expired_count: int
    total_available_units: int


# ── Lotes próximos a vencer (Batch TypeScript con medication embebido) ────────

class EnrichedBatchResponse(BaseModel):
    """Espejo de la interfaz Batch del frontend, con campo medication."""
    id: str
    fk_medication_id: str
    medication: MedicationOptionResponse
    fk_supplier_id: Optional[str] = None
    supplier_name: Optional[str] = None
    lot_number: str
    expiration_date: str
    quantity_received: int
    quantity_available: int
    unit_cost: Optional[float] = None
    batch_status: str
    received_at: str


class ExpirationReportResponse(BaseModel):
    """Espejo de la interfaz ExpirationReport del frontend."""
    generated_at: str
    threshold_days: int
    batches: List[EnrichedBatchResponse]


# ── Consumo mensual (ConsumptionReport TypeScript) ────────────────────────────

class ConsumptionItemResponse(BaseModel):
    """Espejo de la interfaz ConsumptionItem del frontend."""
    medication_id: str
    generic_name: str
    total_dispatched: int
    dispatch_count: int
    patient_count: int


class ConsumptionReportResponse(BaseModel):
    """Espejo de la interfaz ConsumptionReport del frontend."""
    period: str  # Formato YYYY-MM
    items: List[ConsumptionItemResponse]


# ── Kardex / Movimientos ──────────────────────────────────────────────────────

class MovementItemResponse(BaseModel):
    movement_date: str
    movement_type: str   # 'entry' | 'exit'
    reference: str
    lot_number: Optional[str] = None
    quantity: int
    unit_cost: Optional[float] = None
    notes: Optional[str] = None


class PaginationMeta(BaseModel):
    total: int
    page: int
    page_size: int
    pages: int


class MovementsReportResponse(BaseModel):
    medication_id: str
    generic_name: str
    items: List[MovementItemResponse]
    pagination: PaginationMeta


# ── Low-stock ─────────────────────────────────────────────────────────────────

class LowStockReportResponse(BaseModel):
    generated_at: str
    items: List[StockItemResponse]
    total: int


# ── Expiring-soon (horizontes 30/60/90) ──────────────────────────────────────

class ExpiringSoonReportResponse(BaseModel):
    generated_at: str
    vencen_en_30: List[EnrichedBatchResponse]
    vencen_en_60: List[EnrichedBatchResponse]
    vencen_en_90: List[EnrichedBatchResponse]
    total: int


# ── Inventory Movements (trazabilidad persistida) ────────────────────────────

class InventoryMovementResponse(BaseModel):
    id: str
    fk_medication_id: str
    medication_name: Optional[str] = None
    fk_batch_id: Optional[str] = None
    fk_dispatch_id: Optional[str] = None
    fk_purchase_order_id: Optional[str] = None
    movement_type: str
    quantity: int
    balance_after: int
    reference: Optional[str] = None
    lot_number: Optional[str] = None
    unit_cost: Optional[float] = None
    notes: Optional[str] = None
    movement_date: str
    created_at: Optional[str] = None
    created_by: Optional[str] = None


class InventoryMovementsListResponse(BaseModel):
    items: List[InventoryMovementResponse]
    pagination: PaginationMeta


# ── Stock Alerts (alertas persistidas) ───────────────────────────────────────

class StockAlertResponse(BaseModel):
    id: str
    fk_medication_id: str
    medication_name: Optional[str] = None
    medication_code: Optional[str] = None
    alert_level: str
    current_stock: int
    threshold: int
    message: str
    detected_at: str
    resolved_at: Optional[str] = None
    resolved_by: Optional[str] = None
    alert_status: str


class StockAlertsListResponse(BaseModel):
    items: List[StockAlertResponse]
    total: int
    active_count: int
    resolved_count: int
