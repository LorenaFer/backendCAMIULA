#!/usr/bin/env python3
"""
Valida que las migraciones Alembic cumplan los estándares del proyecto.

Checks:
  1. upgrade() presente y no vacío
  2. downgrade() presente y no vacío  (migraciones reversibles)
  3. revision y down_revision declarados
  4. Naming convention: prefijo de fecha/hash + descripción
  5. Sin op.execute() con DDL raw en upgrade/downgrade
  6. Estándar de orden de columnas en op.create_table():
       id → {fk_*} → {data} → {is_* / has_* / *_status} → status → {*_at / *_by}
  7. FK sin prefijo fk_: advertencia (estándar exige fk_patient_id, no patient_id)
  8. Columnas obligatorias en op.create_table(): status + trazabilidad
  9. op.add_column() NOT NULL sin server_default → VIOLACIÓN (fallará en producción)
 10. op.drop_column / op.alter_column sobre columnas de auditoría → VIOLACIÓN

Uso:
  python scripts/validate_migrations.py
  python scripts/validate_migrations.py --strict   # warnings → errores
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

VERSIONS_DIR = Path("alembic/versions")
NAMING_RE = re.compile(r"^(\d{8,14}|[0-9a-f]{12,})_[a-z0-9_]+\.py$")

errors: list[str] = []
warnings: list[str] = []
strict = "--strict" in sys.argv

# Columnas de auditoría/mixins que no se deben tocar
AUDIT_COLS = frozenset({
    "status",
    "created_at", "created_by",
    "updated_at", "updated_by",
    "deleted_at", "deleted_by",
})

# ── Estándar de columnas ──────────────────────────────────────
#
# Grupo | Descripción                  | Ejemplos
# ------+------------------------------+----------------------------
#   0   | Primary key                  | id
#   1   | Foreign keys (prefijo fk_)   | fk_patient_id, fk_doctor_id
#   2   | Datos de negocio             | name, birth_date, amount
#   3   | Flags / estados de dominio   | is_new, has_allergy, appt_status
#   4   | Status general del registro  | status  (siempre "A"/"I"/"T")
#   5   | Trazabilidad (audit trail)   | created_at/by, updated_at/by, deleted_at/by
#
COLUMN_GROUPS = {
    0: "id (PK)",
    1: "foreign keys (fk_*)",
    2: "datos de dominio",
    3: "flags / estados (is_*, has_*, *_status)",
    4: "status general",
    5: "trazabilidad (*_at, *_by)",
}


def _column_group(name: str) -> int:
    if name == "id":
        return 0
    if name.startswith("fk_"):        # fk_patient_id, fk_doctor_id …
        return 1
    if name.endswith("_id"):          # patient_id sin prefijo fk_ → igual grupo 1 (orden)
        return 1
    if name in ("created_at", "created_by",
                "updated_at", "updated_by",
                "deleted_at", "deleted_by"):
        return 5
    if name.endswith(("_at", "_by")):  # cualquier otro audit
        return 5
    if name == "status":              # indicador A/I/T del registro
        return 4
    if (name.startswith(("is_", "has_"))
            or name.endswith("_status")):  # is_new, appt_status …
        return 3
    return 2                          # datos de negocio


def _check_column_order(table_name: str, columns: list[str], fname: str) -> None:
    """
    Verifica que las columnas sigan el estándar de orden y nomenclatura.
    Orden incorrecto → ADVERTENCIA (G03 = warning en db-standards.md).
    """
    prev_group = -1
    prev_name = "(inicio)"
    for col in columns:
        g = _column_group(col)
        if g < prev_group:
            warnings.append(
                f"{fname}: tabla '{table_name}' — columna '{col}' "
                f"(grupo {g}: {COLUMN_GROUPS[g]}) aparece después de "
                f"'{prev_name}' (grupo {prev_group}: {COLUMN_GROUPS[prev_group]}). "
                f"Orden esperado: id → fk_* → datos → flags/status → status → _at/_by"
            )
            return  # reportar solo el primer problema por tabla
        prev_group = g
        prev_name = col

    # ── M06: FK sin prefijo fk_ ───────────────────────────────
    for col in columns:
        if col != "id" and col.endswith("_id") and not col.startswith("fk_"):
            warnings.append(
                f"{fname}: tabla '{table_name}' — columna FK '{col}' "
                f"debería usar prefijo 'fk_' (ej: fk_{col}). "
                f"Estándar: fk_patient_id, fk_doctor_id"
            )

    # ── G02: Columnas obligatorias ────────────────────────────
    names = set(columns)
    if "id" not in names:
        warnings.append(f"{fname}: tabla '{table_name}' no tiene columna 'id'")
    if "status" not in names:
        errors.append(
            f"{fname}: tabla '{table_name}' falta columna 'status' — "
            "requerida por SoftDeleteMixin (A/I/T)"
        )
    audit_required = {"created_at", "created_by", "updated_at", "updated_by"}
    missing_audit = audit_required - names
    if missing_audit:
        # Solo error si NO hay spread *AUDIT_COLS (ya fueron filtrados antes de llegar aquí)
        errors.append(
            f"{fname}: tabla '{table_name}' faltan columnas de auditoría: "
            f"{sorted(missing_audit)} — requeridas por AuditMixin"
        )


def _extract_create_tables(upgrade_body: list[ast.stmt]) -> list[tuple[str, list[str]]]:
    """
    Extrae (table_name, [col_names]) de cada op.create_table() en upgrade().
    Si la tabla usa *AUDIT_COLS (spread) asume que las columnas obligatorias
    están cubiertas y no genera error de columnas faltantes.
    """
    results = []
    for node in ast.walk(ast.Module(body=upgrade_body, type_ignores=[])):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not (isinstance(func, ast.Attribute) and func.attr == "create_table"):
            continue
        if not node.args or not isinstance(node.args[0], ast.Constant):
            continue
        table_name = node.args[0].value

        col_names: list[str] = []
        has_spread = False
        for arg in node.args[1:]:
            if isinstance(arg, ast.Starred):
                has_spread = True
                continue
            if not isinstance(arg, ast.Call):
                continue
            col_func = arg.func
            is_column_call = (
                (isinstance(col_func, ast.Attribute) and col_func.attr == "Column")
                or (isinstance(col_func, ast.Name) and col_func.id == "Column")
            )
            if not is_column_call:
                continue
            if not arg.args or not isinstance(arg.args[0], ast.Constant):
                continue
            col_names.append(arg.args[0].value)

        if col_names:
            results.append((table_name, col_names, has_spread))
    return results  # type: ignore[return-value]


def _check_add_column_not_null(upgrade_body: list[ast.stmt], fname: str) -> None:
    """
    G07: op.add_column() con NOT NULL y sin server_default → VIOLACIÓN.
    Fallará en producción si la tabla ya tiene datos.
    """
    for node in ast.walk(ast.Module(body=upgrade_body, type_ignores=[])):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not (isinstance(func, ast.Attribute) and func.attr == "add_column"):
            continue
        # Buscar el Column(...) dentro del add_column
        for arg in node.args:
            if not isinstance(arg, ast.Call):
                continue
            col_func = arg.func
            is_col = (
                (isinstance(col_func, ast.Attribute) and col_func.attr == "Column")
                or (isinstance(col_func, ast.Name) and col_func.id == "Column")
            )
            if not is_col:
                continue
            # Revisar nullable=False y ausencia de server_default
            nullable_false = False
            has_server_default = False
            for kw in arg.keywords:
                if kw.arg == "nullable" and isinstance(kw.value, ast.Constant) and kw.value.value is False:
                    nullable_false = True
                if kw.arg == "server_default":
                    has_server_default = True
            if nullable_false and not has_server_default:
                # Obtener nombre de columna si está disponible
                col_name = "(desconocido)"
                if arg.args and isinstance(arg.args[0], ast.Constant):
                    col_name = arg.args[0].value
                errors.append(
                    f"{fname}: op.add_column() agrega columna NOT NULL '{col_name}' "
                    f"sin server_default — fallará en producción si la tabla tiene datos. "
                    f"Agrega server_default='valor' o nullable=True"
                )


def _check_no_audit_drop_alter(body: list[ast.stmt], fname: str) -> None:
    """
    G08: op.drop_column / op.alter_column sobre columnas de auditoría → VIOLACIÓN.
    Nunca modificar columnas de los mixins (status, created_at, etc.).
    """
    for node in ast.walk(ast.Module(body=body, type_ignores=[])):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not isinstance(func, ast.Attribute):
            continue
        if func.attr not in ("drop_column", "alter_column"):
            continue
        # Segundo arg (o kwarg 'column_name') es el nombre de columna
        col_name = None
        if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
            col_name = node.args[1].value
        else:
            for kw in node.keywords:
                if kw.arg == "column_name" and isinstance(kw.value, ast.Constant):
                    col_name = kw.value.value
        if col_name and col_name in AUDIT_COLS:
            errors.append(
                f"{fname}: op.{func.attr}(..., '{col_name}') — "
                f"las columnas de auditoría/mixins nunca deben modificarse. "
                f"Columnas protegidas: {sorted(AUDIT_COLS)}"
            )


# ── Helpers ───────────────────────────────────────────────────

def _get_function(tree: ast.Module, name: str) -> ast.FunctionDef | None:
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    return None


def _is_only_pass(body: list[ast.stmt]) -> bool:
    return len(body) == 1 and isinstance(body[0], (ast.Pass, ast.Expr))


def _has_raw_ddl(body: list[ast.stmt]) -> bool:
    DDL_KEYWORDS = re.compile(r"\b(CREATE|DROP|ALTER|TRUNCATE)\b", re.I)
    for node in ast.walk(ast.Module(body=body, type_ignores=[])):
        if isinstance(node, ast.Call):
            if (
                isinstance(node.func, ast.Attribute)
                and node.func.attr == "execute"
                and node.args
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)
                and DDL_KEYWORDS.search(node.args[0].value)
            ):
                return True
    return False


# ── Main loop ─────────────────────────────────────────────────

files = sorted(VERSIONS_DIR.glob("*.py"))
files = [f for f in files if not f.name.startswith("_")]

if not files:
    print("⚠️  No se encontraron migraciones en alembic/versions/")
    sys.exit(0)

revisions_seen: dict[str, str] = {}

for mf in files:
    source = mf.read_text(encoding="utf-8")
    fname = mf.name

    # ── Naming convention ────────────────────────────────────
    if not NAMING_RE.match(fname):
        warnings.append(
            f"{fname}: nombre no sigue la convención "
            f"'YYYYMMDD_descripcion.py' o 'hash_descripcion.py'"
        )

    # ── Parse ────────────────────────────────────────────────
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        errors.append(f"{fname}: error de sintaxis — {e}")
        continue

    # ── upgrade() ────────────────────────────────────────────
    upgrade_fn = _get_function(tree, "upgrade")
    if upgrade_fn is None:
        errors.append(f"{fname}: falta la función upgrade()")
    elif _is_only_pass(upgrade_fn.body):
        errors.append(f"{fname}: upgrade() está vacío")

    # ── downgrade() reversible ───────────────────────────────
    downgrade_fn = _get_function(tree, "downgrade")
    if downgrade_fn is None:
        errors.append(f"{fname}: falta la función downgrade()")
    elif _is_only_pass(downgrade_fn.body):
        errors.append(
            f"{fname}: downgrade() está vacío — "
            "todas las migraciones deben ser reversibles"
        )

    # ── Sin DDL raw ──────────────────────────────────────────
    if upgrade_fn and _has_raw_ddl(upgrade_fn.body):
        warnings.append(
            f"{fname}: upgrade() usa op.execute() con DDL raw. "
            "Prefiere op.create_table() / op.add_column() para trazabilidad."
        )

    # ── revision / down_revision ─────────────────────────────
    rev_match = re.search(
        r'^revision\s*(?::\s*\w+\s*)?=\s*["\'](.+?)["\']', source, re.M
    )
    if not rev_match:
        errors.append(f"{fname}: no se encontró 'revision = ...'")
    else:
        rev_id = rev_match.group(1)
        if rev_id in revisions_seen:
            errors.append(
                f"{fname}: revision '{rev_id}' duplicada "
                f"(ya usada en {revisions_seen[rev_id]})"
            )
        revisions_seen[rev_id] = fname

    if not re.search(r'^down_revision\s*(?::.+?)?\s*=', source, re.M):
        errors.append(f"{fname}: no se encontró 'down_revision = ...'")

    # ── Estándar de orden de columnas + columnas obligatorias ─
    if upgrade_fn:
        for table_name, col_names, has_spread in _extract_create_tables(upgrade_fn.body):
            # Si usa *AUDIT_COLS/spread, las columnas obligatorias están cubiertas
            if has_spread:
                # Tabla usa *AUDIT_COLS spread → columnas obligatorias cubiertas.
                # Solo verificar orden de columnas explícitas (G03 = warning).
                prev_group = -1
                prev_name = "(inicio)"
                for col in col_names:
                    g = _column_group(col)
                    if g < prev_group:
                        warnings.append(
                            f"{fname}: tabla '{table_name}' — columna '{col}' "
                            f"(grupo {g}: {COLUMN_GROUPS[g]}) aparece después de "
                            f"'{prev_name}' (grupo {prev_group}: {COLUMN_GROUPS[prev_group]}). "
                            f"Orden esperado: id → fk_* → datos → flags/status → status → _at/_by"
                        )
                        break
                    prev_group = g
                    prev_name = col
                # M06: FK sin prefijo
                for col in col_names:
                    if col != "id" and col.endswith("_id") and not col.startswith("fk_"):
                        warnings.append(
                            f"{fname}: tabla '{table_name}' — columna FK '{col}' "
                            f"debería usar prefijo 'fk_' (ej: fk_{col})"
                        )
            else:
                _check_column_order(table_name, col_names, fname)

        # ── G07: add_column NOT NULL sin server_default ──────
        _check_add_column_not_null(upgrade_fn.body, fname)

    # ── G08: drop/alter sobre columnas de auditoría ──────────
    for fn in (upgrade_fn, downgrade_fn):
        if fn:
            _check_no_audit_drop_alter(fn.body, fname)


# ── Resumen ───────────────────────────────────────────────────
print(f"\n{'='*62}")
print(f"  Validación de migraciones — {len(files)} archivo(s)")
print(f"{'='*62}")
print(
    "\n  Estándar de columnas:\n"
    "  id → {fk_*} → {datos} → {is_*/has_*/*_status} → status → {*_at/*_by}\n"
)

if warnings:
    print(f"⚠️  Warnings ({len(warnings)}):")
    for w in warnings:
        print(f"   · {w}")

if errors:
    print(f"\n❌ Errores ({len(errors)}):")
    for e in errors:
        print(f"   · {e}")
    print("\nCorrige los errores antes de hacer deploy.\n")
    sys.exit(1)

if strict and warnings:
    print("\n❌ --strict activo: warnings tratados como errores.\n")
    sys.exit(1)

print(f"✅ Todas las migraciones cumplen los estándares.\n")
sys.exit(0)
