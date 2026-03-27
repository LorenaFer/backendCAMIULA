"""
Modelos SQLAlchemy del módulo de Inventario.

Todas las tablas siguen el estándar de columnas del proyecto:
    id → fk_* → dominio → {tabla}_status → status → audit

Referencia: docs/06-estandar-base-de-datos.md
"""

from __future__ import annotations

import enum
from datetime import date, datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import Boolean, Date, DateTime, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.database.base import Base
from app.shared.database.mixins import AuditMixin, SoftDeleteMixin


# ─────────────────────────────────────────────────────────────
# ENUMS DE NEGOCIO
# ─────────────────────────────────────────────────────────────


class SupplierStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class MedicationStatus(str, enum.Enum):
    ACTIVE = "active"
    DISCONTINUED = "discontinued"
    PENDING = "pending"


class PurchaseOrderStatus(str, enum.Enum):
    DRAFT = "draft"
    SENT = "sent"
    PARTIAL = "partial"
    RECEIVED = "received"
    CANCELLED = "cancelled"


class PurchaseOrderItemStatus(str, enum.Enum):
    PENDING = "pending"
    PARTIAL = "partial"
    RECEIVED = "received"
    CANCELLED = "cancelled"


class BatchStatus(str, enum.Enum):
    AVAILABLE = "available"
    DEPLETED = "depleted"
    EXPIRED = "expired"
    QUARANTINE = "quarantine"


class PrescriptionStatus(str, enum.Enum):
    DRAFT = "draft"
    ISSUED = "issued"
    DISPENSED = "dispensed"
    CANCELLED = "cancelled"


class PrescriptionItemStatus(str, enum.Enum):
    PENDING = "pending"
    PARTIAL = "partial"
    DISPENSED = "dispensed"
    UNAVAILABLE = "unavailable"


class DispatchStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class LimitAppliesTo(str, enum.Enum):
    ALL = "all"
    STUDENT = "student"
    EMPLOYEE = "employee"
    PROFESSOR = "professor"


# ─────────────────────────────────────────────────────────────
# PILAR 1 — SUPPLIERS
# ─────────────────────────────────────────────────────────────


class SupplierModel(Base, SoftDeleteMixin, AuditMixin):
    """Proveedor de medicamentos e insumos médicos."""

    __tablename__ = "suppliers"

    # 1. Identidad
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    # 3. Dominio
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    rif: Mapped[str] = mapped_column(
        String(20), nullable=False, unique=True, index=True
    )
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    email: Mapped[Optional[str]] = mapped_column(String(200))
    contact_name: Mapped[Optional[str]] = mapped_column(String(200))
    payment_terms: Mapped[Optional[str]] = mapped_column(String(500))

    # 4. Estado de negocio
    supplier_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=SupplierStatus.ACTIVE,
    )

    # 5-8. status + audit → proporcionados por los mixins


# ─────────────────────────────────────────────────────────────
# PILAR 1 — MEDICATIONS
# ─────────────────────────────────────────────────────────────


class MedicationModel(Base, SoftDeleteMixin, AuditMixin):
    """Catálogo maestro de medicamentos e insumos médicos."""

    __tablename__ = "medications"

    # 1. Identidad
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    # 3. Dominio
    code: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True, index=True
    )
    generic_name: Mapped[str] = mapped_column(
        String(200), nullable=False, index=True
    )
    commercial_name: Mapped[Optional[str]] = mapped_column(String(200))
    pharmaceutical_form: Mapped[str] = mapped_column(String(100), nullable=False)
    concentration: Mapped[Optional[str]] = mapped_column(String(100))
    unit_measure: Mapped[str] = mapped_column(String(50), nullable=False)
    therapeutic_class: Mapped[Optional[str]] = mapped_column(String(100))
    controlled_substance: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    requires_refrigeration: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )

    # 4. Estado de negocio
    medication_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=MedicationStatus.ACTIVE,
        index=True,
    )

    # 5-8. status + audit → proporcionados por los mixins


# ─────────────────────────────────────────────────────────────
# PILAR 1 — PURCHASE ORDERS
# ─────────────────────────────────────────────────────────────


class PurchaseOrderModel(Base, SoftDeleteMixin, AuditMixin):
    """Orden de compra emitida a un proveedor."""

    __tablename__ = "purchase_orders"

    # 1. Identidad
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    # 2. Relaciones
    fk_supplier_id: Mapped[str] = mapped_column(
        String(36), nullable=False, index=True
    )

    # 3. Dominio
    order_number: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True, index=True
    )
    order_date: Mapped[date] = mapped_column(Date, nullable=False)
    expected_date: Mapped[Optional[date]] = mapped_column(Date)
    notes: Mapped[Optional[str]] = mapped_column(String(500))

    # 4. Estado de negocio
    order_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=PurchaseOrderStatus.DRAFT,
        index=True,
    )

    # 5-8. status + audit → proporcionados por los mixins


class PurchaseOrderItemModel(Base, SoftDeleteMixin, AuditMixin):
    """Ítem de una orden de compra (medicamento + cantidades)."""

    __tablename__ = "purchase_order_items"

    # 1. Identidad
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    # 2. Relaciones
    fk_purchase_order_id: Mapped[str] = mapped_column(
        String(36), nullable=False, index=True
    )
    fk_medication_id: Mapped[str] = mapped_column(
        String(36), nullable=False, index=True
    )

    # 3. Dominio
    quantity_ordered: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity_received: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    unit_cost: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))

    # 4. Estado de negocio
    item_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=PurchaseOrderItemStatus.PENDING,
    )

    # 5-8. status + audit → proporcionados por los mixins


# ─────────────────────────────────────────────────────────────
# PILAR 1 — BATCHES (LOTES)
# ─────────────────────────────────────────────────────────────


class BatchModel(Base, SoftDeleteMixin, AuditMixin):
    """Lote de medicamento recibido en almacén."""

    __tablename__ = "batches"

    # 1. Identidad
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    # 2. Relaciones
    fk_medication_id: Mapped[str] = mapped_column(
        String(36), nullable=False, index=True
    )
    fk_supplier_id: Mapped[Optional[str]] = mapped_column(String(36), index=True)
    fk_purchase_order_id: Mapped[Optional[str]] = mapped_column(
        String(36), index=True
    )

    # 3. Dominio
    lot_number: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    expiration_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    quantity_received: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity_available: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_cost: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    received_at: Mapped[date] = mapped_column(Date, nullable=False)

    # 4. Estado de negocio
    batch_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=BatchStatus.AVAILABLE,
        index=True,
    )

    # 5-8. status + audit → proporcionados por los mixins


# ─────────────────────────────────────────────────────────────
# PILAR 2 — PRESCRIPTIONS (RECETAS MÉDICAS)
# ─────────────────────────────────────────────────────────────


class PrescriptionModel(Base, SoftDeleteMixin, AuditMixin):
    """Receta médica emitida durante una consulta."""

    __tablename__ = "prescriptions"

    # 1. Identidad
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    # 2. Relaciones (FK lógicas entre módulos — sin ForeignKey() de BD)
    fk_appointment_id: Mapped[str] = mapped_column(
        String(36), nullable=False, index=True
    )
    fk_patient_id: Mapped[str] = mapped_column(
        String(36), nullable=False, index=True
    )
    fk_doctor_id: Mapped[str] = mapped_column(
        String(36), nullable=False, index=True
    )

    # 3. Dominio
    prescription_number: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True, index=True
    )
    prescription_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    notes: Mapped[Optional[str]] = mapped_column(String(500))

    # 4. Estado de negocio
    prescription_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=PrescriptionStatus.DRAFT,
        index=True,
    )

    # 5-8. status + audit → proporcionados por los mixins


class PrescriptionItemModel(Base, SoftDeleteMixin, AuditMixin):
    """Ítem de una receta médica (medicamento prescrito)."""

    __tablename__ = "prescription_items"

    # 1. Identidad
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    # 2. Relaciones
    fk_prescription_id: Mapped[str] = mapped_column(
        String(36), nullable=False, index=True
    )
    fk_medication_id: Mapped[str] = mapped_column(
        String(36), nullable=False, index=True
    )

    # 3. Dominio
    quantity_prescribed: Mapped[int] = mapped_column(Integer, nullable=False)
    dosage_instructions: Mapped[Optional[str]] = mapped_column(String(300))
    duration_days: Mapped[Optional[int]] = mapped_column(Integer)
    quantity_dispatched: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )

    # 4. Estado de negocio
    item_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=PrescriptionItemStatus.PENDING,
    )

    # 5-8. status + audit → proporcionados por los mixins


# ─────────────────────────────────────────────────────────────
# PILAR 2 — DISPATCHES (DESPACHOS DE FARMACIA)
# ─────────────────────────────────────────────────────────────


class DispatchModel(Base, SoftDeleteMixin, AuditMixin):
    """Acto de despacho de medicamentos en farmacia."""

    __tablename__ = "dispatches"

    # 1. Identidad
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    # 2. Relaciones
    fk_prescription_id: Mapped[str] = mapped_column(
        String(36), nullable=False, index=True
    )
    fk_patient_id: Mapped[str] = mapped_column(
        String(36), nullable=False, index=True
    )
    fk_pharmacist_id: Mapped[str] = mapped_column(
        String(36), nullable=False, index=True
    )

    # 3. Dominio
    dispatch_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    notes: Mapped[Optional[str]] = mapped_column(String(500))

    # 4. Estado de negocio
    dispatch_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=DispatchStatus.PENDING,
        index=True,
    )

    # 5-8. status + audit → proporcionados por los mixins


class DispatchItemModel(Base, SoftDeleteMixin, AuditMixin):
    """Ítem de un despacho con trazabilidad de lote."""

    __tablename__ = "dispatch_items"

    # 1. Identidad
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    # 2. Relaciones
    fk_dispatch_id: Mapped[str] = mapped_column(
        String(36), nullable=False, index=True
    )
    fk_batch_id: Mapped[str] = mapped_column(
        String(36), nullable=False, index=True
    )
    fk_medication_id: Mapped[str] = mapped_column(
        String(36), nullable=False, index=True
    )

    # 3. Dominio
    quantity_dispatched: Mapped[int] = mapped_column(Integer, nullable=False)

    # 5-8. status + audit → proporcionados por los mixins


# ─────────────────────────────────────────────────────────────
# PILAR 3 — DISPATCH LIMITS & EXCEPTIONS
# ─────────────────────────────────────────────────────────────


class DispatchLimitModel(Base, SoftDeleteMixin, AuditMixin):
    """Límite mensual de despacho por medicamento y tipo de beneficiario."""

    __tablename__ = "dispatch_limits"

    # 1. Identidad
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    # 2. Relaciones
    fk_medication_id: Mapped[str] = mapped_column(
        String(36), nullable=False, index=True
    )

    # 3. Dominio
    monthly_max_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    applies_to: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=LimitAppliesTo.ALL,
        index=True,
    )
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # 5-8. status + audit → proporcionados por los mixins


class DispatchExceptionModel(Base, SoftDeleteMixin, AuditMixin):
    """Excepción autorizada al límite de despacho para un paciente específico."""

    __tablename__ = "dispatch_exceptions"

    # 1. Identidad
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    # 2. Relaciones (FK lógicas entre módulos)
    fk_patient_id: Mapped[str] = mapped_column(
        String(36), nullable=False, index=True
    )
    fk_medication_id: Mapped[str] = mapped_column(
        String(36), nullable=False, index=True
    )

    # 3. Dominio
    authorized_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    valid_from: Mapped[date] = mapped_column(Date, nullable=False)
    valid_until: Mapped[date] = mapped_column(Date, nullable=False)
    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    authorized_by: Mapped[Optional[str]] = mapped_column(String(200))

    # 5-8. status + audit → proporcionados por los mixins
