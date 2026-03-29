"""init_inventory_ula_single_tenant

Revision ID: 202603262351
Revises: 5926bb76aef3
Create Date: 2026-03-26

Crea las 11 tablas del módulo de Inventario CAMIULA (sistema single-tenant ULA).
No existe ninguna columna de tenant_id: el sistema es exclusivo para la ULA.

Checklist antes de aplicar:
- [ ] CREATE TABLE: orden id → fk_* → datos → table_status → status → auditoría
- [ ] ALTER TABLE: modelo Python actualizado con columna en grupo correcto
- [ ] Columnas NOT NULL tienen server_default si la tabla tiene datos
- [ ] downgrade() revierte los cambios correctamente
- [ ] Columnas de auditoría/status NO fueron modificadas ni eliminadas

Ver: docs/06-estandar-base-de-datos.md
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "202603262351"
down_revision = "5926bb76aef3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ─────────────────────────────────────────────
    # PILAR 1 — suppliers
    # ─────────────────────────────────────────────
    op.create_table(
        "suppliers",
        sa.Column("id", sa.String(36), primary_key=True),
        # domain
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("rif", sa.String(20), nullable=False),
        sa.Column("phone", sa.String(20)),
        sa.Column("email", sa.String(200)),
        sa.Column("contact_name", sa.String(200)),
        sa.Column("payment_terms", sa.String(500)),
        # business status
        sa.Column("supplier_status", sa.String(20), nullable=False, server_default="active"),
        # technical control
        sa.Column("status", postgresql.ENUM("A", "I", "T", name="record_status", create_type=False), nullable=False, server_default="A"),
        # audit
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("created_by", sa.String(36)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.Column("updated_by", sa.String(36)),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("deleted_by", sa.String(36)),
    )
    op.create_index("ix_suppliers_rif", "suppliers", ["rif"], unique=True)
    op.create_index("ix_suppliers_status", "suppliers", ["status"])

    # ─────────────────────────────────────────────
    # PILAR 1 — medications
    # ─────────────────────────────────────────────
    op.create_table(
        "medications",
        sa.Column("id", sa.String(36), primary_key=True),
        # domain
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("generic_name", sa.String(200), nullable=False),
        sa.Column("commercial_name", sa.String(200)),
        sa.Column("pharmaceutical_form", sa.String(100), nullable=False),
        sa.Column("concentration", sa.String(100)),
        sa.Column("unit_measure", sa.String(50), nullable=False),
        sa.Column("therapeutic_class", sa.String(100)),
        sa.Column("controlled_substance", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("requires_refrigeration", sa.Boolean(), nullable=False, server_default="false"),
        # business status
        sa.Column("medication_status", sa.String(20), nullable=False, server_default="active"),
        # technical control
        sa.Column("status", postgresql.ENUM("A", "I", "T", name="record_status", create_type=False), nullable=False, server_default="A"),
        # audit
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("created_by", sa.String(36)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.Column("updated_by", sa.String(36)),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("deleted_by", sa.String(36)),
    )
    op.create_index("ix_medications_code", "medications", ["code"], unique=True)
    op.create_index("ix_medications_generic_name", "medications", ["generic_name"])
    op.create_index("ix_medications_medication_status", "medications", ["medication_status"])
    op.create_index("ix_medications_status", "medications", ["status"])

    # ─────────────────────────────────────────────
    # PILAR 1 — purchase_orders
    # ─────────────────────────────────────────────
    op.create_table(
        "purchase_orders",
        sa.Column("id", sa.String(36), primary_key=True),
        # relations
        sa.Column("fk_supplier_id", sa.String(36), sa.ForeignKey("suppliers.id"), nullable=False),
        # domain
        sa.Column("order_number", sa.String(50), nullable=False),
        sa.Column("order_date", sa.Date(), nullable=False),
        sa.Column("expected_date", sa.Date()),
        sa.Column("notes", sa.String(500)),
        # business status
        sa.Column("order_status", sa.String(20), nullable=False, server_default="draft"),
        # technical control
        sa.Column("status", postgresql.ENUM("A", "I", "T", name="record_status", create_type=False), nullable=False, server_default="A"),
        # audit
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("created_by", sa.String(36)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.Column("updated_by", sa.String(36)),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("deleted_by", sa.String(36)),
    )
    op.create_index("ix_purchase_orders_fk_supplier_id", "purchase_orders", ["fk_supplier_id"])
    op.create_index("ix_purchase_orders_order_number", "purchase_orders", ["order_number"], unique=True)
    op.create_index("ix_purchase_orders_order_status", "purchase_orders", ["order_status"])
    op.create_index("ix_purchase_orders_status", "purchase_orders", ["status"])

    # ─────────────────────────────────────────────
    # PILAR 1 — purchase_order_items
    # ─────────────────────────────────────────────
    op.create_table(
        "purchase_order_items",
        sa.Column("id", sa.String(36), primary_key=True),
        # relations
        sa.Column("fk_purchase_order_id", sa.String(36), sa.ForeignKey("purchase_orders.id"), nullable=False),
        sa.Column("fk_medication_id", sa.String(36), sa.ForeignKey("medications.id"), nullable=False),
        # domain
        sa.Column("quantity_ordered", sa.Integer(), nullable=False),
        sa.Column("quantity_received", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("unit_cost", sa.Numeric(10, 2)),
        # business status
        sa.Column("item_status", sa.String(20), nullable=False, server_default="pending"),
        # technical control
        sa.Column("status", postgresql.ENUM("A", "I", "T", name="record_status", create_type=False), nullable=False, server_default="A"),
        # audit
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("created_by", sa.String(36)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.Column("updated_by", sa.String(36)),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("deleted_by", sa.String(36)),
    )
    op.create_index("ix_purchase_order_items_fk_purchase_order_id", "purchase_order_items", ["fk_purchase_order_id"])
    op.create_index("ix_purchase_order_items_fk_medication_id", "purchase_order_items", ["fk_medication_id"])
    op.create_index("ix_purchase_order_items_status", "purchase_order_items", ["status"])

    # ─────────────────────────────────────────────
    # PILAR 1 — batches
    # ─────────────────────────────────────────────
    op.create_table(
        "batches",
        sa.Column("id", sa.String(36), primary_key=True),
        # relations
        sa.Column("fk_medication_id", sa.String(36), sa.ForeignKey("medications.id"), nullable=False),
        sa.Column("fk_supplier_id", sa.String(36), sa.ForeignKey("suppliers.id")),
        sa.Column("fk_purchase_order_id", sa.String(36), sa.ForeignKey("purchase_orders.id")),
        # domain
        sa.Column("lot_number", sa.String(100), nullable=False),
        sa.Column("expiration_date", sa.Date(), nullable=False),
        sa.Column("quantity_received", sa.Integer(), nullable=False),
        sa.Column("quantity_available", sa.Integer(), nullable=False),
        sa.Column("unit_cost", sa.Numeric(10, 2)),
        sa.Column("received_at", sa.Date(), nullable=False),
        # business status
        sa.Column("batch_status", sa.String(20), nullable=False, server_default="available"),
        # technical control
        sa.Column("status", postgresql.ENUM("A", "I", "T", name="record_status", create_type=False), nullable=False, server_default="A"),
        # audit
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("created_by", sa.String(36)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.Column("updated_by", sa.String(36)),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("deleted_by", sa.String(36)),
    )
    op.create_index("ix_batches_fk_medication_id", "batches", ["fk_medication_id"])
    op.create_index("ix_batches_fk_supplier_id", "batches", ["fk_supplier_id"])
    op.create_index("ix_batches_fk_purchase_order_id", "batches", ["fk_purchase_order_id"])
    op.create_index("ix_batches_lot_number", "batches", ["lot_number"])
    op.create_index("ix_batches_expiration_date", "batches", ["expiration_date"])
    op.create_index("ix_batches_batch_status", "batches", ["batch_status"])
    op.create_index("ix_batches_status", "batches", ["status"])

    # Índice compuesto FEFO: consulta crítica del despacho
    op.create_index(
        "ix_batches_medication_fefo",
        "batches",
        ["fk_medication_id", "expiration_date"],
        postgresql_where=sa.text("batch_status = 'available' AND status = 'A'"),
    )

    # ─────────────────────────────────────────────
    # PILAR 2 — prescriptions
    # ─────────────────────────────────────────────
    op.create_table(
        "prescriptions",
        sa.Column("id", sa.String(36), primary_key=True),
        # relations (FK lógicas entre módulos — sin FK de BD)
        sa.Column("fk_appointment_id", sa.String(36), nullable=False),
        sa.Column("fk_patient_id", sa.String(36), nullable=False),
        sa.Column("fk_doctor_id", sa.String(36), nullable=False),
        # domain
        sa.Column("prescription_number", sa.String(50), nullable=False),
        sa.Column("prescription_date", sa.Date(), nullable=False),
        sa.Column("notes", sa.String(500)),
        # business status
        sa.Column("prescription_status", sa.String(20), nullable=False, server_default="draft"),
        # technical control
        sa.Column("status", postgresql.ENUM("A", "I", "T", name="record_status", create_type=False), nullable=False, server_default="A"),
        # audit
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("created_by", sa.String(36)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.Column("updated_by", sa.String(36)),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("deleted_by", sa.String(36)),
    )
    op.create_index("ix_prescriptions_fk_appointment_id", "prescriptions", ["fk_appointment_id"])
    op.create_index("ix_prescriptions_fk_patient_id", "prescriptions", ["fk_patient_id"])
    op.create_index("ix_prescriptions_fk_doctor_id", "prescriptions", ["fk_doctor_id"])
    op.create_index("ix_prescriptions_prescription_number", "prescriptions", ["prescription_number"], unique=True)
    op.create_index("ix_prescriptions_prescription_date", "prescriptions", ["prescription_date"])
    op.create_index("ix_prescriptions_prescription_status", "prescriptions", ["prescription_status"])
    op.create_index("ix_prescriptions_status", "prescriptions", ["status"])

    # ─────────────────────────────────────────────
    # PILAR 2 — prescription_items
    # ─────────────────────────────────────────────
    op.create_table(
        "prescription_items",
        sa.Column("id", sa.String(36), primary_key=True),
        # relations
        sa.Column("fk_prescription_id", sa.String(36), sa.ForeignKey("prescriptions.id"), nullable=False),
        sa.Column("fk_medication_id", sa.String(36), sa.ForeignKey("medications.id"), nullable=False),
        # domain
        sa.Column("quantity_prescribed", sa.Integer(), nullable=False),
        sa.Column("dosage_instructions", sa.String(300)),
        sa.Column("duration_days", sa.Integer()),
        sa.Column("quantity_dispatched", sa.Integer(), nullable=False, server_default="0"),
        # business status
        sa.Column("item_status", sa.String(20), nullable=False, server_default="pending"),
        # technical control
        sa.Column("status", postgresql.ENUM("A", "I", "T", name="record_status", create_type=False), nullable=False, server_default="A"),
        # audit
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("created_by", sa.String(36)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.Column("updated_by", sa.String(36)),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("deleted_by", sa.String(36)),
    )
    op.create_index("ix_prescription_items_fk_prescription_id", "prescription_items", ["fk_prescription_id"])
    op.create_index("ix_prescription_items_fk_medication_id", "prescription_items", ["fk_medication_id"])
    op.create_index("ix_prescription_items_status", "prescription_items", ["status"])

    # ─────────────────────────────────────────────
    # PILAR 2 — dispatches
    # ─────────────────────────────────────────────
    op.create_table(
        "dispatches",
        sa.Column("id", sa.String(36), primary_key=True),
        # relations
        sa.Column("fk_prescription_id", sa.String(36), sa.ForeignKey("prescriptions.id"), nullable=False),
        # relations (FK lógicas entre módulos — sin FK de BD)
        sa.Column("fk_patient_id", sa.String(36), nullable=False),
        sa.Column("fk_pharmacist_id", sa.String(36), nullable=False),
        # domain
        sa.Column("dispatch_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("notes", sa.String(500)),
        # business status
        sa.Column("dispatch_status", sa.String(20), nullable=False, server_default="pending"),
        # technical control
        sa.Column("status", postgresql.ENUM("A", "I", "T", name="record_status", create_type=False), nullable=False, server_default="A"),
        # audit
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("created_by", sa.String(36)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.Column("updated_by", sa.String(36)),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("deleted_by", sa.String(36)),
    )
    op.create_index("ix_dispatches_fk_prescription_id", "dispatches", ["fk_prescription_id"])
    op.create_index("ix_dispatches_fk_patient_id", "dispatches", ["fk_patient_id"])
    op.create_index("ix_dispatches_fk_pharmacist_id", "dispatches", ["fk_pharmacist_id"])
    op.create_index("ix_dispatches_dispatch_date", "dispatches", ["dispatch_date"])
    op.create_index("ix_dispatches_dispatch_status", "dispatches", ["dispatch_status"])
    op.create_index("ix_dispatches_status", "dispatches", ["status"])

    # Índice compuesto para cálculo de consumo mensual por paciente
    op.create_index(
        "ix_dispatches_patient_date",
        "dispatches",
        ["fk_patient_id", "dispatch_date"],
    )

    # ─────────────────────────────────────────────
    # PILAR 2 — dispatch_items
    # ─────────────────────────────────────────────
    op.create_table(
        "dispatch_items",
        sa.Column("id", sa.String(36), primary_key=True),
        # relations
        sa.Column("fk_dispatch_id", sa.String(36), sa.ForeignKey("dispatches.id"), nullable=False),
        sa.Column("fk_batch_id", sa.String(36), sa.ForeignKey("batches.id"), nullable=False),
        sa.Column("fk_medication_id", sa.String(36), sa.ForeignKey("medications.id"), nullable=False),
        # domain
        sa.Column("quantity_dispatched", sa.Integer(), nullable=False),
        # technical control
        sa.Column("status", postgresql.ENUM("A", "I", "T", name="record_status", create_type=False), nullable=False, server_default="A"),
        # audit
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("created_by", sa.String(36)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.Column("updated_by", sa.String(36)),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("deleted_by", sa.String(36)),
    )
    op.create_index("ix_dispatch_items_fk_dispatch_id", "dispatch_items", ["fk_dispatch_id"])
    op.create_index("ix_dispatch_items_fk_batch_id", "dispatch_items", ["fk_batch_id"])
    op.create_index("ix_dispatch_items_fk_medication_id", "dispatch_items", ["fk_medication_id"])
    op.create_index("ix_dispatch_items_status", "dispatch_items", ["status"])

    # ─────────────────────────────────────────────
    # PILAR 3 — dispatch_limits
    # ─────────────────────────────────────────────
    op.create_table(
        "dispatch_limits",
        sa.Column("id", sa.String(36), primary_key=True),
        # relations
        sa.Column("fk_medication_id", sa.String(36), sa.ForeignKey("medications.id"), nullable=False),
        # domain
        sa.Column("monthly_max_quantity", sa.Integer(), nullable=False),
        sa.Column("applies_to", sa.String(20), nullable=False, server_default="all"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default="true"),
        # technical control
        sa.Column("status", postgresql.ENUM("A", "I", "T", name="record_status", create_type=False), nullable=False, server_default="A"),
        # audit
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("created_by", sa.String(36)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.Column("updated_by", sa.String(36)),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("deleted_by", sa.String(36)),
    )
    op.create_index("ix_dispatch_limits_fk_medication_id", "dispatch_limits", ["fk_medication_id"])
    op.create_index("ix_dispatch_limits_applies_to", "dispatch_limits", ["applies_to"])
    op.create_index("ix_dispatch_limits_status", "dispatch_limits", ["status"])

    # Índice compuesto para validación de límites en despacho
    op.create_index(
        "ix_dispatch_limits_medication_applies",
        "dispatch_limits",
        ["fk_medication_id", "applies_to"],
        postgresql_where=sa.text("active = true AND status = 'A'"),
    )

    # ─────────────────────────────────────────────
    # PILAR 3 — dispatch_exceptions
    # ─────────────────────────────────────────────
    op.create_table(
        "dispatch_exceptions",
        sa.Column("id", sa.String(36), primary_key=True),
        # relations (FK lógicas entre módulos — sin FK de BD)
        sa.Column("fk_patient_id", sa.String(36), nullable=False),
        # relations
        sa.Column("fk_medication_id", sa.String(36), sa.ForeignKey("medications.id"), nullable=False),
        # domain
        sa.Column("authorized_quantity", sa.Integer(), nullable=False),
        sa.Column("valid_from", sa.Date(), nullable=False),
        sa.Column("valid_until", sa.Date(), nullable=False),
        sa.Column("reason", sa.String(500), nullable=False),
        sa.Column("authorized_by", sa.String(200)),
        # technical control
        sa.Column("status", postgresql.ENUM("A", "I", "T", name="record_status", create_type=False), nullable=False, server_default="A"),
        # audit
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("created_by", sa.String(36)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.Column("updated_by", sa.String(36)),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("deleted_by", sa.String(36)),
    )
    op.create_index("ix_dispatch_exceptions_fk_patient_id", "dispatch_exceptions", ["fk_patient_id"])
    op.create_index("ix_dispatch_exceptions_fk_medication_id", "dispatch_exceptions", ["fk_medication_id"])
    op.create_index("ix_dispatch_exceptions_status", "dispatch_exceptions", ["status"])


def downgrade() -> None:
    op.drop_table("dispatch_exceptions")
    op.drop_table("dispatch_limits")
    op.drop_table("dispatch_items")
    op.drop_table("dispatches")
    op.drop_table("prescription_items")
    op.drop_table("prescriptions")
    op.drop_table("batches")
    op.drop_table("purchase_order_items")
    op.drop_table("purchase_orders")
    op.drop_table("medications")
    op.drop_table("suppliers")
