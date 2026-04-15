"""add revoked_tokens table for JWT logout/rotation

Revision ID: 20260415_revtok
Revises: 20260407_apptoken
Create Date: 2026-04-15

Tabla de revocación de JWTs. Cada entrada representa un token que fue
explícitamente invalidado (logout, rotación de refresh) antes de expirar.

El middleware de auth consulta esta tabla por (jti) en cada request autenticado.
Índice único sobre jti para O(log n) lookup.

Limpieza: los registros con expires_at < now() pueden purgarse con un cron
o en el arranque del backend — no afectan la correctitud, solo el tamaño.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260415_revtok"
down_revision: Union[str, None] = "20260407_apptoken"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "revoked_tokens",
        sa.Column("jti", sa.String(length=36), primary_key=True),
        sa.Column("fk_user_id", sa.String(length=36), nullable=False),
        sa.Column(
            "revoked_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("token_type", sa.String(length=20), nullable=False),
    )
    op.create_index(
        "ix_revoked_tokens_expires_at",
        "revoked_tokens",
        ["expires_at"],
    )
    op.create_index(
        "ix_revoked_tokens_user",
        "revoked_tokens",
        ["fk_user_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_revoked_tokens_user", table_name="revoked_tokens")
    op.drop_index("ix_revoked_tokens_expires_at", table_name="revoked_tokens")
    op.drop_table("revoked_tokens")
