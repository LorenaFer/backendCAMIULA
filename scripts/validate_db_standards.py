#!/usr/bin/env python3
"""Validador de estándares de base de datos para modelos SQLAlchemy.

Verifica que cada modelo cumpla con:
1. Orden de columnas: id → fk_* → dominio → table_status → status → audit
2. Herencia de mixins: SoftDeleteMixin + AuditMixin
3. Columna id es String(36) PK
4. Naming conventions de FK: fk_{tabla}_{columna}
5. Indices en columnas de filtro

Uso:
    python scripts/validate_db_standards.py
"""

import importlib
import inspect
import sys
from pathlib import Path

# Agregar raíz del proyecto al path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sqlalchemy import inspect as sa_inspect
from sqlalchemy.orm import Mapped

from app.shared.database.base import Base
from app.shared.database.mixins import AuditMixin, SoftDeleteMixin

# ── Importar todos los modelos ────────────────────────────────

MODEL_MODULES = [
    "app.modules.auth.infrastructure.models",
    "app.modules.patients.infrastructure.models",
    "app.modules.inventory.infrastructure.models",
]

for mod_path in MODEL_MODULES:
    try:
        importlib.import_module(mod_path)
    except ImportError as e:
        print(f"⚠ No se pudo importar {mod_path}: {e}")

# ── Grupos de columnas esperados ──────────────────────────────

AUDIT_COLUMNS = {
    "status",
    "created_at", "created_by",
    "updated_at", "updated_by",
    "deleted_at", "deleted_by",
}

EXPECTED_ORDER = [
    "identity",     # id
    "relations",    # fk_*
    "domain",       # datos propios
    "biz_status",   # {table}_status
    "tech_status",  # status (A/I/T)
    "audit_create", # created_at, created_by
    "audit_update", # updated_at, updated_by
    "audit_delete", # deleted_at, deleted_by
]


def classify_column(col_name: str, table_name: str) -> str:
    """Clasifica una columna en su grupo esperado."""
    if col_name == "id":
        return "identity"
    if col_name.startswith("fk_"):
        return "relations"
    if col_name == "status":
        return "tech_status"
    # Only the table's own business status column (e.g. patient_status for patients)
    # follows the convention {singular_table_name}_status
    singular = table_name.rstrip("s")
    if col_name == f"{singular}_status":
        return "biz_status"
    if col_name == "created_at" or col_name == "created_by":
        return "audit_create"
    if col_name == "updated_at" or col_name == "updated_by":
        return "audit_update"
    if col_name == "deleted_at" or col_name == "deleted_by":
        return "audit_delete"
    return "domain"


def validate_column_order(model_cls) -> list[str]:
    """Valida que las columnas estén en el orden estándar."""
    errors = []
    table_name = model_cls.__tablename__

    # Obtener columnas en orden de definición
    mapper = sa_inspect(model_cls)
    columns = [c.key for c in mapper.columns]

    # Clasificar cada columna
    groups = [classify_column(col, table_name) for col in columns]

    # Verificar que los grupos estén en orden no-decreciente
    group_indices = {g: i for i, g in enumerate(EXPECTED_ORDER)}
    last_idx = -1
    last_group = ""

    for col, group in zip(columns, groups):
        idx = group_indices.get(group, 3)  # domain = 3 por defecto
        if idx < last_idx:
            errors.append(
                f"  Columna '{col}' (grupo: {group}) está después de "
                f"'{last_group}' — debería estar antes."
            )
        last_idx = idx
        last_group = group

    return errors


def validate_mixins(model_cls) -> list[str]:
    """Verifica que el modelo herede SoftDeleteMixin y AuditMixin."""
    errors = []
    if not issubclass(model_cls, SoftDeleteMixin):
        errors.append("  No hereda SoftDeleteMixin")
    if not issubclass(model_cls, AuditMixin):
        errors.append("  No hereda AuditMixin")
    return errors


def validate_pk(model_cls) -> list[str]:
    """Verifica que id sea String(36) PK."""
    errors = []
    mapper = sa_inspect(model_cls)
    pk_cols = [c for c in mapper.columns if c.primary_key]
    if not pk_cols:
        errors.append("  No tiene primary key")
    elif pk_cols[0].key != "id":
        errors.append(f"  PK se llama '{pk_cols[0].key}' en vez de 'id'")
    return errors


def validate_fk_naming(model_cls) -> list[str]:
    """Verifica que las FKs sigan el patrón fk_{tabla}_{columna}."""
    errors = []
    mapper = sa_inspect(model_cls)
    for col in mapper.columns:
        if col.foreign_keys and not col.key.startswith("fk_"):
            errors.append(
                f"  Columna '{col.key}' tiene FK pero no sigue patrón fk_*"
            )
    return errors


def validate_indices(model_cls) -> list[str]:
    """Verifica que columnas de status y FK tengan índice."""
    warnings = []
    mapper = sa_inspect(model_cls)
    indexed_cols = set()

    table = model_cls.__table__
    for idx in table.indexes:
        for col in idx.columns:
            indexed_cols.add(col.key)

    for col in mapper.columns:
        if col.key == "status" and col.key not in indexed_cols:
            warnings.append(f"  ⚠ Columna 'status' sin índice")
        if col.key.startswith("fk_") and col.key not in indexed_cols:
            warnings.append(f"  ⚠ FK '{col.key}' sin índice")

    return warnings


def main():
    print("═══════════════════════════════════════════")
    print("  Validador de Estándares de Base de Datos")
    print("═══════════════════════════════════════════\n")

    total_errors = 0
    total_warnings = 0
    models_checked = 0

    for cls in Base.__subclasses__():
        if not hasattr(cls, "__tablename__"):
            continue

        # Saltar modelos abstractos o mixins
        if inspect.isabstract(cls):
            continue

        models_checked += 1
        table = cls.__tablename__
        errors = []
        warnings = []

        errors.extend(validate_mixins(cls))
        errors.extend(validate_pk(cls))
        errors.extend(validate_column_order(cls))
        errors.extend(validate_fk_naming(cls))
        warnings.extend(validate_indices(cls))

        if errors or warnings:
            print(f"{'✘' if errors else '⚠'} {table} ({cls.__name__})")
            for e in errors:
                print(f"  \033[31m{e}\033[0m")
                total_errors += 1
            for w in warnings:
                print(f"  \033[33m{w}\033[0m")
                total_warnings += 1
        else:
            print(f"✔ {table} ({cls.__name__})")

    print(f"\n{'═' * 43}")
    print(f"  Modelos verificados: {models_checked}")
    print(f"  Errores: {total_errors}")
    print(f"  Advertencias: {total_warnings}")
    print(f"{'═' * 43}")

    return 1 if total_errors > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
