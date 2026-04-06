"""add_inventory_movements_and_stock_alerts_tables

Revision ID: 948fcff75cb4
Revises: 20260402_patients
Create Date: 2026-04-05 16:58:10.434050

Checklist antes de aplicar:
- [x] CREATE TABLE: orden id → fk_* → datos → table_status → status → auditoría
- [x] ALTER TABLE: modelo Python actualizado con columna en grupo correcto
- [x] Columnas NOT NULL tienen server_default si la tabla tiene datos
- [x] downgrade() revierte los cambios correctamente
- [x] Columnas de auditoría/status NO fueron modificadas ni eliminadas

Ver: docs/06-estandar-base-de-datos.md
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '948fcff75cb4'
down_revision: Union[str, None] = '20260402_patients'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── inventory_movements ──────────────────────────────────
    op.create_table('inventory_movements',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('fk_medication_id', sa.String(length=36), nullable=False),
    sa.Column('fk_batch_id', sa.String(length=36), nullable=True),
    sa.Column('fk_dispatch_id', sa.String(length=36), nullable=True),
    sa.Column('fk_purchase_order_id', sa.String(length=36), nullable=True),
    sa.Column('movement_type', sa.String(length=20), nullable=False),
    sa.Column('quantity', sa.Integer(), nullable=False),
    sa.Column('balance_after', sa.Integer(), nullable=False),
    sa.Column('reference', sa.String(length=200), nullable=True),
    sa.Column('lot_number', sa.String(length=100), nullable=True),
    sa.Column('unit_cost', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('notes', sa.String(length=500), nullable=True),
    sa.Column('movement_date', sa.DateTime(timezone=True), nullable=False),
    sa.Column('status', sa.Enum('A', 'I', 'T', name='record_status', create_type=False), server_default=sa.text("'A'::record_status"), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('created_by', sa.String(length=36), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_by', sa.String(length=36), nullable=True),
    sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('deleted_by', sa.String(length=36), nullable=True),
    sa.ForeignKeyConstraint(['fk_batch_id'], ['batches.id']),
    sa.ForeignKeyConstraint(['fk_dispatch_id'], ['dispatches.id']),
    sa.ForeignKeyConstraint(['fk_medication_id'], ['medications.id']),
    sa.ForeignKeyConstraint(['fk_purchase_order_id'], ['purchase_orders.id']),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_inventory_movements_fk_medication_id', 'inventory_movements', ['fk_medication_id'])
    op.create_index('ix_inventory_movements_fk_batch_id', 'inventory_movements', ['fk_batch_id'])
    op.create_index('ix_inventory_movements_fk_dispatch_id', 'inventory_movements', ['fk_dispatch_id'])
    op.create_index('ix_inventory_movements_fk_purchase_order_id', 'inventory_movements', ['fk_purchase_order_id'])
    op.create_index('ix_inventory_movements_movement_type', 'inventory_movements', ['movement_type'])
    op.create_index('ix_inventory_movements_movement_date', 'inventory_movements', ['movement_date'])
    op.create_index('ix_inventory_movements_status', 'inventory_movements', ['status'])

    # ── stock_alerts ─────────────────────────────────────────
    op.create_table('stock_alerts',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('fk_medication_id', sa.String(length=36), nullable=False),
    sa.Column('alert_level', sa.String(length=20), nullable=False),
    sa.Column('current_stock', sa.Integer(), nullable=False),
    sa.Column('threshold', sa.Integer(), nullable=False),
    sa.Column('message', sa.String(length=500), nullable=False),
    sa.Column('detected_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('resolved_by', sa.String(length=36), nullable=True),
    sa.Column('alert_status', sa.String(length=20), nullable=False),
    sa.Column('status', sa.Enum('A', 'I', 'T', name='record_status', create_type=False), server_default=sa.text("'A'::record_status"), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('created_by', sa.String(length=36), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_by', sa.String(length=36), nullable=True),
    sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('deleted_by', sa.String(length=36), nullable=True),
    sa.ForeignKeyConstraint(['fk_medication_id'], ['medications.id']),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_stock_alerts_fk_medication_id', 'stock_alerts', ['fk_medication_id'])
    op.create_index('ix_stock_alerts_alert_level', 'stock_alerts', ['alert_level'])
    op.create_index('ix_stock_alerts_alert_status', 'stock_alerts', ['alert_status'])
    op.create_index('ix_stock_alerts_detected_at', 'stock_alerts', ['detected_at'])
    op.create_index('ix_stock_alerts_status', 'stock_alerts', ['status'])


def downgrade() -> None:
    op.drop_table('stock_alerts')
    op.drop_table('inventory_movements')
