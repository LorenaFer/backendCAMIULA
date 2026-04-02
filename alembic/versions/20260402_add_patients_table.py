"""add_patients_age_column — add missing 'age' column and new indices

Revision ID: 20260402_patients
Revises: 202603262351
Create Date: 2026-04-02

The patients table already exists from the init migration.
This adds the missing 'age' column and new indices.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260402_patients"
down_revision: Union[str, None] = "202603262351"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # Add 'age' column if it doesn't exist
    result = conn.execute(
        sa.text(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name = 'patients' AND column_name = 'age'"
        )
    )
    if not result.fetchone():
        op.add_column("patients", sa.Column("age", sa.Integer, nullable=True))

    # Add indices if they don't exist
    for idx_name, columns in [
        ("ix_patients_last_name", ["last_name"]),
        ("ix_patients_university_relation", ["university_relation"]),
        ("ix_patients_patient_status", ["patient_status"]),
    ]:
        result = conn.execute(
            sa.text(f"SELECT 1 FROM pg_indexes WHERE indexname = '{idx_name}'")
        )
        if not result.fetchone():
            op.create_index(idx_name, "patients", columns)


def downgrade() -> None:
    conn = op.get_bind()

    for idx_name in [
        "ix_patients_patient_status",
        "ix_patients_university_relation",
        "ix_patients_last_name",
    ]:
        result = conn.execute(
            sa.text(f"SELECT 1 FROM pg_indexes WHERE indexname = '{idx_name}'")
        )
        if result.fetchone():
            op.drop_index(idx_name, table_name="patients")

    result = conn.execute(
        sa.text(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name = 'patients' AND column_name = 'age'"
        )
    )
    if result.fetchone():
        op.drop_column("patients", "age")
