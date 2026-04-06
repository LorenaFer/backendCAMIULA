"""create missing tables: patients, doctors, specialties, appointments, medical_records

Revision ID: 20260402_patients
Revises: 202603262351
Create Date: 2026-04-02

Creates all tables that were previously created outside Alembic:
patients, specialties, doctors, doctor_availability, doctor_exceptions,
appointments, medical_records, form_schemas, medical_orders.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260402_patients"
down_revision: Union[str, None] = "202603262351"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(conn, name):
    r = conn.execute(sa.text(
        "SELECT 1 FROM information_schema.tables WHERE table_name = :n AND table_schema = 'public'"
    ), {"n": name})
    return r.fetchone() is not None


def upgrade() -> None:
    conn = op.get_bind()

    # ── PATIENTS ─────────────────────────────────────────
    if not _table_exists(conn, "patients"):
        op.create_table("patients",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("fk_holder_patient_id", sa.String(36), nullable=True),
            sa.Column("nhm", sa.Integer, nullable=False, unique=True),
            sa.Column("dni", sa.String(20), nullable=False, unique=True),
            sa.Column("first_name", sa.String(100), nullable=False),
            sa.Column("last_name", sa.String(100), nullable=False),
            sa.Column("sex", sa.String(1), nullable=True),
            sa.Column("birth_date", sa.Date, nullable=True),
            sa.Column("birth_place", sa.String(200), nullable=True),
            sa.Column("marital_status", sa.String(20), nullable=True),
            sa.Column("religion", sa.String(100), nullable=True),
            sa.Column("origin", sa.String(200), nullable=True),
            sa.Column("home_address", sa.String(300), nullable=True),
            sa.Column("phone", sa.String(20), nullable=True),
            sa.Column("profession", sa.String(100), nullable=True),
            sa.Column("current_occupation", sa.String(100), nullable=True),
            sa.Column("work_address", sa.String(300), nullable=True),
            sa.Column("economic_classification", sa.String(50), nullable=True),
            sa.Column("university_relation", sa.String(20), nullable=False),
            sa.Column("family_relationship", sa.String(20), nullable=True),
            sa.Column("medical_data", sa.JSON, nullable=False, server_default="{}"),
            sa.Column("emergency_contact", sa.JSON, nullable=True),
            sa.Column("is_new", sa.Boolean, nullable=False, server_default="true"),
            sa.Column("patient_status", sa.String(30), nullable=False, server_default="active"),
            sa.Column("status", sa.String(1), nullable=False, server_default="A")),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("created_by", sa.String(36), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("updated_by", sa.String(36), nullable=True),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("deleted_by", sa.String(36), nullable=True),
        )
        op.create_index("ix_patients_nhm", "patients", ["nhm"], unique=True)
        op.create_index("ix_patients_dni", "patients", ["dni"], unique=True)

    # Add extra indices if missing
    for idx, cols in [("ix_patients_last_name", ["last_name"]), ("ix_patients_university_relation", ["university_relation"]), ("ix_patients_patient_status", ["patient_status"])]:
        r = conn.execute(sa.text(f"SELECT 1 FROM pg_indexes WHERE indexname = '{idx}'"))
        if not r.fetchone():
            op.create_index(idx, "patients", cols)

    # ── SPECIALTIES ──────────────────────────────────────
    if not _table_exists(conn, "specialties"):
        op.create_table("specialties",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("name", sa.String(200), nullable=False),
            sa.Column("status", sa.String(1), nullable=False, server_default="A")),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("created_by", sa.String(36), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("updated_by", sa.String(36), nullable=True),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("deleted_by", sa.String(36), nullable=True),
        )

    # ── DOCTORS ──────────────────────────────────────────
    if not _table_exists(conn, "doctors"):
        op.create_table("doctors",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("fk_user_id", sa.String(36), nullable=False),
            sa.Column("fk_specialty_id", sa.String(36), nullable=False),
            sa.Column("first_name", sa.String(100), nullable=False),
            sa.Column("last_name", sa.String(100), nullable=False),
            sa.Column("doctor_status", sa.String(20), nullable=False, server_default="ACTIVE"),
            sa.Column("status", sa.String(1), nullable=False, server_default="A")),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("created_by", sa.String(36), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("updated_by", sa.String(36), nullable=True),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("deleted_by", sa.String(36), nullable=True),
        )

    # ── DOCTOR_AVAILABILITY ──────────────────────────────
    if not _table_exists(conn, "doctor_availability"):
        op.create_table("doctor_availability",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("fk_doctor_id", sa.String(36), nullable=False),
            sa.Column("day_of_week", sa.Integer, nullable=False),
            sa.Column("start_time", sa.Time, nullable=False),
            sa.Column("end_time", sa.Time, nullable=False),
            sa.Column("slot_duration", sa.Integer, nullable=False, server_default="30"),
            sa.Column("status", sa.String(1), nullable=False, server_default="A")),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("created_by", sa.String(36), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("updated_by", sa.String(36), nullable=True),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("deleted_by", sa.String(36), nullable=True),
        )

    # ── DOCTOR_EXCEPTIONS ────────────────────────────────
    if not _table_exists(conn, "doctor_exceptions"):
        op.create_table("doctor_exceptions",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("fk_doctor_id", sa.String(36), nullable=False),
            sa.Column("exception_date", sa.Date, nullable=False),
            sa.Column("reason", sa.String(500), nullable=True),
            sa.Column("status", sa.String(1), nullable=False, server_default="A")),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("created_by", sa.String(36), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("updated_by", sa.String(36), nullable=True),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("deleted_by", sa.String(36), nullable=True),
        )

    # ── APPOINTMENTS ─────────────────────────────────────
    if not _table_exists(conn, "appointments"):
        op.create_table("appointments",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("fk_patient_id", sa.String(36), nullable=False),
            sa.Column("fk_doctor_id", sa.String(36), nullable=False),
            sa.Column("fk_specialty_id", sa.String(36), nullable=False),
            sa.Column("appointment_date", sa.Date, nullable=False),
            sa.Column("start_time", sa.Time, nullable=False),
            sa.Column("end_time", sa.Time, nullable=False),
            sa.Column("duration_minutes", sa.Integer, nullable=False),
            sa.Column("is_first_visit", sa.Boolean, nullable=False, server_default="false"),
            sa.Column("reason", sa.String(500), nullable=True),
            sa.Column("observations", sa.String(500), nullable=True),
            sa.Column("appointment_status", sa.String(20), nullable=False, server_default="pendiente"),
            sa.Column("status", sa.String(1), nullable=False, server_default="A")),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("created_by", sa.String(36), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("updated_by", sa.String(36), nullable=True),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("deleted_by", sa.String(36), nullable=True),
        )
        op.create_index("ix_appointments_fk_patient_id", "appointments", ["fk_patient_id"])
        op.create_index("ix_appointments_fk_doctor_id", "appointments", ["fk_doctor_id"])
        op.create_index("ix_appointments_appointment_date", "appointments", ["appointment_date"])

    # ── MEDICAL_RECORDS ──────────────────────────────────
    if not _table_exists(conn, "medical_records"):
        op.create_table("medical_records",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("fk_appointment_id", sa.String(36), nullable=False),
            sa.Column("fk_patient_id", sa.String(36), nullable=False),
            sa.Column("fk_doctor_id", sa.String(36), nullable=False),
            sa.Column("evaluation", sa.JSON, nullable=True),
            sa.Column("is_prepared", sa.Boolean, nullable=False, server_default="false"),
            sa.Column("prepared_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("prepared_by", sa.String(36), nullable=True),
            sa.Column("schema_id", sa.String(36), nullable=True),
            sa.Column("schema_version", sa.String(50), nullable=True),
            sa.Column("status", sa.String(1), nullable=False, server_default="A")),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("created_by", sa.String(36), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("updated_by", sa.String(36), nullable=True),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("deleted_by", sa.String(36), nullable=True),
        )
        op.create_index("ix_medical_records_fk_appointment_id", "medical_records", ["fk_appointment_id"])
        op.create_index("ix_medical_records_fk_patient_id", "medical_records", ["fk_patient_id"])

    # ── FORM_SCHEMAS ─────────────────────────────────────
    if not _table_exists(conn, "form_schemas"):
        op.create_table("form_schemas",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("specialty_id", sa.String(36), nullable=False),
            sa.Column("specialty_name", sa.String(200), nullable=False),
            sa.Column("specialty_key", sa.String(200), nullable=True, unique=True),
            sa.Column("version", sa.String(50), nullable=False),
            sa.Column("schema_json", sa.JSON, nullable=True),
            sa.Column("status", sa.String(1), nullable=False, server_default="A")),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("created_by", sa.String(36), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("updated_by", sa.String(36), nullable=True),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("deleted_by", sa.String(36), nullable=True),
        )

    # ── MEDICAL_ORDERS ───────────────────────────────────
    if not _table_exists(conn, "medical_orders"):
        op.create_table("medical_orders",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("fk_appointment_id", sa.String(36), nullable=False),
            sa.Column("fk_patient_id", sa.String(36), nullable=False),
            sa.Column("fk_doctor_id", sa.String(36), nullable=False),
            sa.Column("order_type", sa.String(50), nullable=True, server_default="exam"),
            sa.Column("exam_name", sa.String(200), nullable=False),
            sa.Column("notes", sa.String(500), nullable=True),
            sa.Column("order_status", sa.String(20), nullable=False, server_default="requested"),
            sa.Column("status", sa.String(1), nullable=False, server_default="A")),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("created_by", sa.String(36), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("updated_by", sa.String(36), nullable=True),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("deleted_by", sa.String(36), nullable=True),
        )



    # Fix status columns: convert VARCHAR(1) -> record_status enum
    # The record_status enum is created by the auth migration (5926bb76aef3)
    tables_to_fix = ["patients", "specialties", "doctors", "doctor_availability",
                     "doctor_exceptions", "appointments", "medical_records",
                     "form_schemas", "medical_orders"]
    for tbl in tables_to_fix:
        if _table_exists(conn, tbl):
            try:
                conn.execute(sa.text(f"ALTER TABLE {tbl} ALTER COLUMN status DROP DEFAULT"))
                conn.execute(sa.text(f"ALTER TABLE {tbl} ALTER COLUMN status TYPE record_status USING status::record_status"))
                conn.execute(sa.text(f"ALTER TABLE {tbl} ALTER COLUMN status SET DEFAULT 'A'::record_status"))
            except Exception:
                pass  # Already correct type


def downgrade() -> None:
    conn = op.get_bind()
    for table in ["medical_orders", "form_schemas", "medical_records", "appointments",
                   "doctor_exceptions", "doctor_availability", "doctors", "specialties", "patients"]:
        if _table_exists(conn, table):
            op.drop_table(table)
