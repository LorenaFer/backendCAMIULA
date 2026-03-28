"""add form_schemas table and schema fields to medical_records

Revision ID: a3f2e1b4c5d6
Revises: 1fbb33d57c3b
Create Date: 2026-03-27 00:00:00.000000

Checklist antes de aplicar:
- [x] CREATE TABLE: orden id → specialty → datos → status → auditoría (AuditMixin)
- [x] ALTER TABLE: modelo Python actualizado con columnas en grupo correcto
- [x] Columnas NOT NULL tienen server_default si la tabla tiene datos
- [x] downgrade() revierte los cambios correctamente
- [x] Columnas de auditoría/status NO fueron modificadas ni eliminadas
- [x] status con enum record_status y default 'A'
- [x] Parejas de auditoría: created_at+created_by, updated_at+updated_by, deleted_at+deleted_by

Ver: docs/06-estandar-base-de-datos.md
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'a3f2e1b4c5d6'
down_revision: Union[str, None] = '1fbb33d57c3b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── 1. Tabla form_schemas ──────────────────────────────────────────────
    # Columnas en el orden estándar del proyecto:
    # Grupo 1: id | Grupo 2: specialty | Grupo 3: dominio |
    # Grupo 5: status | Grupos 6-8: auditoría (AuditMixin)
    # Nota: record_status enum ya existe en la DB (creado por la migración anterior).
    # Usamos postgresql.ENUM con create_type=False para reutilizarlo.
    record_status = postgresql.ENUM('A', 'I', 'T', name='record_status', create_type=False)
    op.create_table(
        'form_schemas',
        # Grupo 1: Identidad (PK semántico)
        sa.Column('id', sa.String(length=100), nullable=False),
        # Grupo 2: Relación con especialidad
        sa.Column('specialty_id', sa.String(length=100), nullable=False),
        sa.Column('specialty_name', sa.String(length=100), nullable=False),
        # Grupo 3: Dominio
        sa.Column('version', sa.String(length=20), nullable=False),
        sa.Column('schema_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        # Grupo 5: Control técnico (SoftDeleteMixin)
        sa.Column(
            'status',
            record_status,
            server_default='A',
            nullable=False,
        ),
        # Grupo 6: Auditoría de creación
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column('created_by', sa.String(length=36), nullable=True),
        # Grupo 7: Auditoría de edición
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', sa.String(length=36), nullable=True),
        # Grupo 8: Auditoría de eliminación (soft-delete)
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', sa.String(length=36), nullable=True),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_form_schemas')),
    )
    with op.batch_alter_table('form_schemas', schema=None) as batch_op:
        batch_op.create_index(
            'ix_form_schemas_specialty_id', ['specialty_id'], unique=False
        )
        batch_op.create_index(
            'ix_form_schemas_status', ['status'], unique=False
        )

    # ── 2. Agregar schema_id y schema_version a medical_records ───────────
    # Columnas nullable (registros existentes no tienen schema)
    with op.batch_alter_table('medical_records', schema=None) as batch_op:
        batch_op.add_column(sa.Column('schema_id', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('schema_version', sa.String(length=20), nullable=True))


def downgrade() -> None:
    # ── Revertir schema_id y schema_version ───────────────────────────────
    with op.batch_alter_table('medical_records', schema=None) as batch_op:
        batch_op.drop_column('schema_version')
        batch_op.drop_column('schema_id')

    # ── Eliminar tabla form_schemas ────────────────────────────────────────
    with op.batch_alter_table('form_schemas', schema=None) as batch_op:
        batch_op.drop_index('ix_form_schemas_status')
        batch_op.drop_index('ix_form_schemas_specialty_id')

    op.drop_table('form_schemas')
