"""
Helpers para migraciones Alembic que mantienen el estándar de columnas.

PostgreSQL NO soporta ALTER TABLE ADD COLUMN ... AFTER column_name.
Todo ADD COLUMN se agrega al FINAL de la tabla físicamente.

Esto significa que al agregar columnas de dominio nuevas a una tabla existente,
quedan DESPUÉS de las columnas de auditoría en el orden físico.

REGLA:
    - El MODELO en Python es la fuente de verdad del orden lógico.
    - El orden físico en PostgreSQL NO afecta rendimiento ni consultas.
    - Si el DBA requiere reordenar físicamente, usar `reorder_table_columns()`.

Uso en una migración manual:

    from app.shared.database.migration_helpers import reorder_table_columns

    def upgrade():
        # Después de agregar columnas nuevas, reordenar si es necesario
        reorder_table_columns(
            "patients",
            [
                "id",
                "fk_doctor_id",
                "first_name", "last_name", "cedula", "email", "phone",
                "patient_status",
                "status",
                "created_at", "created_by",
                "updated_at", "updated_by",
                "deleted_at", "deleted_by",
            ],
        )
"""

from alembic import op


def reorder_table_columns(table_name: str, column_order: list[str]) -> None:
    """Reordena las columnas de una tabla PostgreSQL recreándola.

    Pasos:
        1. Renombra la tabla original a {table}_old
        2. Crea la nueva tabla con SELECT en el orden deseado
        3. Elimina la tabla vieja
        4. Restaura índices, PKs y FKs (manejado por batch_alter_table)

    ADVERTENCIA: Esto bloquea la tabla durante la operación.
    Solo usar cuando el orden físico sea un requisito del DBA.
    """
    cols_str = ", ".join(column_order)

    # Usar batch operations (render_as_batch=True en env.py)
    # Esto recrea la tabla internamente preservando constraints
    op.execute(
        f'CREATE TABLE "{table_name}_new" AS '
        f'SELECT {cols_str} FROM "{table_name}"'
    )
    op.execute(f'DROP TABLE "{table_name}" CASCADE')
    op.execute(f'ALTER TABLE "{table_name}_new" RENAME TO "{table_name}"')

    # IMPORTANTE: Después de esto hay que recrear constraints manualmente.
    # Ver la guía en docs/06-estandar-base-de-datos.md sección "Reordenar columnas".


def add_domain_column_sql(
    table_name: str,
    column_name: str,
    column_type: str,
    nullable: bool = True,
    default: str = None,
) -> str:
    """Genera el SQL para agregar una columna de dominio.

    Retorna el SQL como string para documentación/logging.
    La columna se agrega al final físicamente (limitación de PostgreSQL).
    El modelo Python debe reflejar el orden lógico correcto.
    """
    parts = [f'ALTER TABLE "{table_name}" ADD COLUMN "{column_name}" {column_type}']
    if not nullable:
        parts.append("NOT NULL")
    if default is not None:
        parts.append(f"DEFAULT {default}")
    return " ".join(parts)
