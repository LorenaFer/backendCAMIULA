"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

Checklist antes de aplicar:
- [ ] CREATE TABLE: orden id → fk_* → datos → table_status → status → auditoría
- [ ] ALTER TABLE: modelo Python actualizado con columna en grupo correcto
- [ ] Columnas NOT NULL tienen server_default si la tabla tiene datos
- [ ] downgrade() revierte los cambios correctamente
- [ ] Columnas de auditoría/status NO fueron modificadas ni eliminadas

Ver: docs/06-estandar-base-de-datos.md
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
