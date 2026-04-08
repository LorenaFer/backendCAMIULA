"""add client_token to appointments for idempotent retries

Revision ID: 20260407_apptoken
Revises: be3983ae3ea6
Create Date: 2026-04-07

Adds an optional client-generated UUID to appointments so that POST /appointments
becomes idempotent: if a network microcut causes the client to retry the same
request, the server returns the previously-created appointment instead of
duplicating it. The UNIQUE index gives O(1) lookup by token.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260407_apptoken"
down_revision: Union[str, None] = "be3983ae3ea6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "appointments",
        sa.Column("client_token", sa.String(length=36), nullable=True),
    )
    op.create_index(
        "ix_appointments_client_token",
        "appointments",
        ["client_token"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_appointments_client_token", table_name="appointments")
    op.drop_column("appointments", "client_token")
