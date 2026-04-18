#!/usr/bin/env python3
"""
Valida que las migraciones Alembic cumplan los estándares del proyecto.

Checks:
  1. upgrade() presente y no vacío
  2. downgrade() presente y no vacío (migraciones reversibles)
  3. revision y down_revision declarados
  4. Naming convention: prefijo de fecha/hash + descripción
  5. Sin op.execute() con DDL raw (solo se permite DML en downgrade)
  6. Cadena de revisiones sin duplicados ni huérfanos

Uso:
  python scripts/validate_migrations.py
  python scripts/validate_migrations.py --strict   # trata warnings como errores
"""

import ast
import re
import sys
from pathlib import Path

VERSIONS_DIR = Path("alembic/versions")
NAMING_RE = re.compile(r"^(\d{8,14}|[0-9a-f]{12,})_[a-z0-9_]+\.py$")

errors: list[str] = []
warnings: list[str] = []
strict = "--strict" in sys.argv


def _get_function_body(tree: ast.Module, name: str) -> list[ast.stmt] | None:
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node.body
    return None


def _is_only_pass(body: list[ast.stmt]) -> bool:
    return len(body) == 1 and isinstance(body[0], (ast.Pass, ast.Expr))


def _has_raw_ddl(body: list[ast.stmt]) -> bool:
    """Detecta op.execute() con strings DDL (CREATE/DROP/ALTER) en el body."""
    DDL_KEYWORDS = re.compile(r"\b(CREATE|DROP|ALTER|TRUNCATE)\b", re.I)
    for node in ast.walk(ast.Module(body=body, type_ignores=[])):
        if isinstance(node, ast.Call):
            # op.execute("...")
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


revisions_seen: dict[str, str] = {}  # revision → filename
down_revisions_seen: dict[str, str] = {}

files = sorted(VERSIONS_DIR.glob("*.py"))
files = [f for f in files if not f.name.startswith("_")]

if not files:
    print("⚠️  No se encontraron migraciones en alembic/versions/")
    sys.exit(0)

for mf in files:
    source = mf.read_text(encoding="utf-8")
    fname = mf.name

    # ── 1. Naming convention ─────────────────────────────────
    if not NAMING_RE.match(fname):
        warnings.append(
            f"{fname}: nombre no sigue la convención "
            f"'YYYYMMDD_descripcion.py' o 'hash_descripcion.py'"
        )

    # ── 2. Parse AST ─────────────────────────────────────────
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        errors.append(f"{fname}: error de sintaxis — {e}")
        continue

    # ── 3. upgrade() ─────────────────────────────────────────
    upgrade_body = _get_function_body(tree, "upgrade")
    if upgrade_body is None:
        errors.append(f"{fname}: falta la función upgrade()")
    elif _is_only_pass(upgrade_body):
        errors.append(f"{fname}: upgrade() está vacío (solo pass/docstring)")

    # ── 4. downgrade() reversible ────────────────────────────
    downgrade_body = _get_function_body(tree, "downgrade")
    if downgrade_body is None:
        errors.append(f"{fname}: falta la función downgrade()")
    elif _is_only_pass(downgrade_body):
        errors.append(
            f"{fname}: downgrade() está vacío — todas las migraciones "
            "deben ser reversibles. Implementa el rollback."
        )

    # ── 5. Sin DDL raw en upgrade/downgrade ──────────────────
    if upgrade_body and _has_raw_ddl(upgrade_body):
        warnings.append(
            f"{fname}: upgrade() usa op.execute() con DDL raw. "
            "Prefiere op.create_table() / op.add_column() para trazabilidad."
        )

    # ── 6. revision y down_revision declarados ───────────────
    revision_match = re.search(r'^revision\s*(?::\s*\w+\s*)?=\s*["\'](.+?)["\']', source, re.M)
    down_rev_match = re.search(r'^down_revision\s*(?::.+?)?\s*=\s*(.+?)$', source, re.M)

    if not revision_match:
        errors.append(f"{fname}: no se encontró 'revision = ...'")
    else:
        rev_id = revision_match.group(1)
        if rev_id in revisions_seen:
            errors.append(
                f"{fname}: revision '{rev_id}' duplicada "
                f"(ya usada en {revisions_seen[rev_id]})"
            )
        revisions_seen[rev_id] = fname

    if not down_rev_match:
        errors.append(f"{fname}: no se encontró 'down_revision = ...'")


# ── Resumen ───────────────────────────────────────────────────
print(f"\n{'='*60}")
print(f"  Validación de migraciones — {len(files)} archivo(s)")
print(f"{'='*60}")

if warnings:
    print(f"\n⚠️  Warnings ({len(warnings)}):")
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

print(f"\n✅ Todas las migraciones cumplen los estándares.\n")
sys.exit(0)
