"""DTOs de solo lectura para reportes de inventario.

Estos DTOs representan vistas agregadas y no corresponden
a entidades de dominio individuales.
"""

from dataclasses import dataclass, field
from typing import List, Optional

# ── Umbrales de alerta de stock (unidades absolutas) ─────────────────────────
# Se aplican tras excluir lotes vencidos de la suma.
STOCK_THRESHOLD_CRITICAL = 10   # ≤ 10 → critical
STOCK_THRESHOLD_LOW = 50        # ≤ 50 → low   (> 10 → ok)


def compute_stock_alert(total_available: int) -> str:
    """Calcula el nivel de alerta de stock según umbrales fijos."""
    if total_available == 0:
        return "expired"
    if total_available <= STOCK_THRESHOLD_CRITICAL:
        return "critical"
    if total_available <= STOCK_THRESHOLD_LOW:
        return "low"
    return "ok"


# ── Stock consolidado (espejo de StockItem TypeScript) ────────────────────────

@dataclass
class StockItemDTO:
    medication_id: str
    code: str
    generic_name: str
    pharmaceutical_form: str
    unit_measure: str
    total_available: int
    batch_count: int
    nearest_expiration: Optional[str]
    days_to_expiration: Optional[int]
    stock_alert: str  # 'ok' | 'low' | 'critical' | 'expired'


@dataclass
class StockReportDTO:
    generated_at: str
    items: List[StockItemDTO]
    total_medications: int
    critical_count: int
    expired_count: int


@dataclass
class LowStockReportDTO:
    generated_at: str
    items: List[StockItemDTO]


# ── Resumen ejecutivo (KPIs del dashboard) ────────────────────────────────────

@dataclass
class InventorySummaryDTO:
    generated_at: str
    total_active_skus: int
    critical_count: int
    low_count: int
    expired_count: int
    total_available_units: int


# ── Lotes próximos a vencer (espejo de Batch TypeScript + enrichment) ─────────

@dataclass
class MedicationOptionDTO:
    id: str
    code: str
    generic_name: str
    pharmaceutical_form: str
    unit_measure: str
    current_stock: int


@dataclass
class EnrichedBatchDTO:
    """Lote con datos de medicamento embebidos (campo `medication`)."""
    id: str
    fk_medication_id: str
    medication: MedicationOptionDTO
    fk_supplier_id: Optional[str]
    supplier_name: Optional[str]
    lot_number: str
    expiration_date: str
    quantity_received: int
    quantity_available: int
    unit_cost: Optional[float]
    batch_status: str
    received_at: str


@dataclass
class ExpirationReportDTO:
    generated_at: str
    threshold_days: int
    batches: List[EnrichedBatchDTO]


# ── Consumo mensual (espejo de ConsumptionReport TypeScript) ──────────────────

@dataclass
class ConsumptionItemDTO:
    medication_id: str
    generic_name: str
    total_dispatched: int
    dispatch_count: int
    patient_count: int


@dataclass
class ConsumptionReportDTO:
    period: str  # Formato YYYY-MM
    items: List[ConsumptionItemDTO]


# ── Kardex / Movimientos ──────────────────────────────────────────────────────

@dataclass
class MovementItemDTO:
    """Una línea del kardex: entrada (lote recibido) o salida (despacho)."""
    movement_date: str           # ISO datetime string
    movement_type: str           # 'entry' | 'exit'
    reference: str               # Número de OC o número de receta
    lot_number: Optional[str]
    quantity: int
    unit_cost: Optional[float]
    notes: Optional[str]


@dataclass
class MovementsReportDTO:
    medication_id: str
    generic_name: str
    items: List[MovementItemDTO] = field(default_factory=list)
    total: int = 0
