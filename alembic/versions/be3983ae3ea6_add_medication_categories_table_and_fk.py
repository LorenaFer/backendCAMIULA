"""add_medication_categories_table_and_fk

Revision ID: be3983ae3ea6
Revises: 948fcff75cb4
Create Date: 2026-04-06 00:05:08.288436

- Creates medication_categories table
- Adds fk_category_id column to medications
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'be3983ae3ea6'
down_revision: Union[str, None] = '948fcff75cb4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create medication_categories table
    op.create_table('medication_categories',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('status', sa.String(length=1),
                  server_default='A', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.String(length=36), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', sa.String(length=36), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', sa.String(length=36), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_medication_categories_name', 'medication_categories', ['name'], unique=True)
    op.create_index('ix_medication_categories_status', 'medication_categories', ['status'])

    # 2. Add fk_category_id to medications (nullable, existing rows get NULL)
    op.add_column('medications', sa.Column('fk_category_id', sa.String(length=36), nullable=True))
    op.create_index('ix_medications_fk_category_id', 'medications', ['fk_category_id'])
    op.create_foreign_key(
        'fk_medications_fk_category_id_medication_categories',
        'medications', 'medication_categories',
        ['fk_category_id'], ['id'],
    )


def downgrade() -> None:
    op.drop_constraint('fk_medications_fk_category_id_medication_categories', 'medications', type_='foreignkey')
    op.drop_index('ix_medications_fk_category_id', table_name='medications')
    op.drop_column('medications', 'fk_category_id')
    op.drop_table('medication_categories')
