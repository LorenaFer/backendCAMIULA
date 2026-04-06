"""rename_patients_cedula_to_dni

Revision ID: 1124e75f3992
Revises: be3983ae3ea6
Create Date: 2026-04-06 02:53:16.230564

Renames the `cedula` column to `dni` in the patients table
for English standardization.
"""
from typing import Sequence, Union

from alembic import op


revision: str = '1124e75f3992'
down_revision: Union[str, None] = 'be3983ae3ea6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('patients', 'cedula', new_column_name='dni')
    # Rename index too
    op.drop_index('ix_patients_cedula', table_name='patients')
    op.create_index('ix_patients_dni', 'patients', ['dni'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_patients_dni', table_name='patients')
    op.create_index('ix_patients_cedula', 'patients', ['cedula'], unique=True)
    op.alter_column('patients', 'dni', new_column_name='cedula')
