"""rename_patients_cedula_to_dni

Revision ID: 1124e75f3992
Revises: be3983ae3ea6
Create Date: 2026-04-06

Renames cedula -> dni on patients table (if column still named cedula).
On fresh DBs the table is already created with 'dni', so this is a no-op.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '1124e75f3992'
down_revision: Union[str, None] = 'be3983ae3ea6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    # Check if column is still named 'cedula' (legacy DBs)
    r = conn.execute(sa.text(
        "SELECT 1 FROM information_schema.columns "
        "WHERE table_name = 'patients' AND column_name = 'cedula'"
    ))
    if r.fetchone():
        op.alter_column('patients', 'cedula', new_column_name='dni')
        # Swap index
        r2 = conn.execute(sa.text("SELECT 1 FROM pg_indexes WHERE indexname = 'ix_patients_cedula'"))
        if r2.fetchone():
            op.drop_index('ix_patients_cedula', table_name='patients')
        r3 = conn.execute(sa.text("SELECT 1 FROM pg_indexes WHERE indexname = 'ix_patients_dni'"))
        if not r3.fetchone():
            op.create_index('ix_patients_dni', 'patients', ['dni'], unique=True)


def downgrade() -> None:
    conn = op.get_bind()
    r = conn.execute(sa.text(
        "SELECT 1 FROM information_schema.columns "
        "WHERE table_name = 'patients' AND column_name = 'dni'"
    ))
    if r.fetchone():
        op.alter_column('patients', 'dni', new_column_name='cedula')
        r2 = conn.execute(sa.text("SELECT 1 FROM pg_indexes WHERE indexname = 'ix_patients_dni'"))
        if r2.fetchone():
            op.drop_index('ix_patients_dni', table_name='patients')
        op.create_index('ix_patients_cedula', 'patients', ['cedula'], unique=True)
