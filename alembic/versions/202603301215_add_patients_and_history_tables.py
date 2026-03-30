"""add_patients_and_history_tables

Revision ID: 202603301215
Revises: 202603262351
Create Date: 2026-03-30

Crea tablas del módulo de pacientes:
- patients
- patient_history_entries
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "202603301215"
down_revision = "202603262351"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "patients",
        sa.Column("id", sa.String(36), primary_key=True),
        # domain
        sa.Column("nhm", sa.Integer(), nullable=False),
        sa.Column("cedula", sa.String(20), nullable=False),
        sa.Column("nombre", sa.String(120), nullable=False),
        sa.Column("apellido", sa.String(120), nullable=False),
        sa.Column("sexo", sa.String(1), nullable=True),
        sa.Column("fecha_nacimiento", sa.Date(), nullable=True),
        sa.Column("lugar_nacimiento", sa.String(120), nullable=True),
        sa.Column("edad", sa.Integer(), nullable=True),
        sa.Column("estado_civil", sa.String(30), nullable=True),
        sa.Column("religion", sa.String(120), nullable=True),
        sa.Column("procedencia", sa.String(120), nullable=True),
        sa.Column("direccion_habitacion", sa.String(255), nullable=True),
        sa.Column("telefono", sa.String(30), nullable=True),
        sa.Column("profesion", sa.String(120), nullable=True),
        sa.Column("ocupacion_actual", sa.String(120), nullable=True),
        sa.Column("direccion_trabajo", sa.String(255), nullable=True),
        sa.Column("clasificacion_economica", sa.String(20), nullable=True),
        sa.Column("relacion_univ", sa.String(20), nullable=False, server_default="tercero"),
        sa.Column("parentesco", sa.String(30), nullable=True),
        sa.Column("titular_nhm", sa.Integer(), nullable=True),
        sa.Column("datos_medicos", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("contacto_emergencia", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("es_nuevo", sa.Boolean(), nullable=False, server_default="true"),
        # business status
        sa.Column("patient_status", sa.String(30), nullable=True, server_default="active"),
        # technical status
        sa.Column("status", sa.Enum("A", "I", "T", name="record_status"), nullable=False, server_default="A"),
        # audit
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("created_by", sa.String(36), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_by", sa.String(36), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", sa.String(36), nullable=True),
    )
    op.create_index("ix_patients_nhm", "patients", ["nhm"], unique=True)
    op.create_index("ix_patients_cedula", "patients", ["cedula"], unique=True)
    op.create_index("ix_patients_titular_nhm", "patients", ["titular_nhm"])
    op.create_index("ix_patients_status", "patients", ["status"])

    op.create_table(
        "patient_history_entries",
        sa.Column("id", sa.String(36), primary_key=True),
        # relations
        sa.Column("fk_patient_id", sa.String(36), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("fk_appointment_id", sa.String(36), nullable=True),
        # domain
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("especialidad", sa.String(120), nullable=True),
        sa.Column("doctor_nombre", sa.String(120), nullable=True),
        sa.Column("diagnostico_descripcion", sa.String(255), nullable=True),
        sa.Column("diagnostico_cie10", sa.String(20), nullable=True),
        # business status
        sa.Column("history_status", sa.String(30), nullable=True, server_default="recorded"),
        # technical status
        sa.Column("status", sa.Enum("A", "I", "T", name="record_status"), nullable=False, server_default="A"),
        # audit
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("created_by", sa.String(36), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_by", sa.String(36), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", sa.String(36), nullable=True),
    )
    op.create_index("ix_patient_history_entries_fk_patient_id", "patient_history_entries", ["fk_patient_id"])
    op.create_index("ix_patient_history_entries_fk_appointment_id", "patient_history_entries", ["fk_appointment_id"])
    op.create_index("ix_patient_history_entries_fecha", "patient_history_entries", ["fecha"])
    op.create_index("ix_patient_history_entries_status", "patient_history_entries", ["status"])


def downgrade() -> None:
    op.drop_index("ix_patient_history_entries_status", table_name="patient_history_entries")
    op.drop_index("ix_patient_history_entries_fecha", table_name="patient_history_entries")
    op.drop_index("ix_patient_history_entries_fk_appointment_id", table_name="patient_history_entries")
    op.drop_index("ix_patient_history_entries_fk_patient_id", table_name="patient_history_entries")
    op.drop_table("patient_history_entries")

    op.drop_index("ix_patients_status", table_name="patients")
    op.drop_index("ix_patients_titular_nhm", table_name="patients")
    op.drop_index("ix_patients_cedula", table_name="patients")
    op.drop_index("ix_patients_nhm", table_name="patients")
    op.drop_table("patients")
