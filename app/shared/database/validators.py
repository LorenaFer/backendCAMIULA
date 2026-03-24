"""
Validador de orden de columnas para modelos SQLAlchemy.

Verifica que un modelo cumpla con el estándar de base de datos:
    id → fk_* → datos → table_status → status → (created_at, created_by) →
    (updated_at, updated_by) → (deleted_at, deleted_by)

Uso en tests:
    from app.shared.database.validators import validate_column_order

    def test_patient_model_column_order():
        violations = validate_column_order(PatientModel)
        assert violations == [], f"Violaciones de orden: {violations}"

Uso como script:
    python -m app.shared.database.validators
"""

from typing import Type

from app.shared.database.base import Base

# Columnas que inyectan los mixins, en el orden esperado
AUDIT_COLUMNS = [
    "created_at", "created_by",
    "updated_at", "updated_by",
    "deleted_at", "deleted_by",
]
STATUS_COLUMN = "status"
MIXIN_COLUMNS = [STATUS_COLUMN] + AUDIT_COLUMNS


def validate_column_order(model_class: Type[Base]) -> list[str]:
    """Valida que las columnas del modelo sigan el estándar.

    Retorna lista vacía si es compliant, o lista de violaciones.
    """
    columns = list(model_class.__table__.columns.keys())
    violations: list[str] = []

    if not columns:
        return ["El modelo no tiene columnas definidas"]

    # --- 1. id debe ser la primera columna ---
    if columns[0] != "id":
        violations.append(
            f"'id' debe ser la primera columna, pero está en posición "
            f"{columns.index('id') + 1}" if "id" in columns else "'id' no existe"
        )

    # --- 2. FKs deben estar justo después de id ---
    fk_cols = [(i, c) for i, c in enumerate(columns) if c.startswith("fk_")]
    if fk_cols:
        first_fk_pos = fk_cols[0][0]
        if first_fk_pos != 1 and len(columns) > 1:
            # Check if there are non-fk columns between id and first fk
            between = columns[1:first_fk_pos]
            non_fk_between = [c for c in between if not c.startswith("fk_")]
            if non_fk_between:
                violations.append(
                    f"FKs deben estar justo después de 'id'. Columnas "
                    f"intermedias: {non_fk_between}"
                )

    # --- 3. status debe estar antes de columnas de auditoría ---
    if STATUS_COLUMN in columns:
        status_pos = columns.index(STATUS_COLUMN)
        for audit_col in AUDIT_COLUMNS:
            if audit_col in columns:
                audit_pos = columns.index(audit_col)
                if status_pos > audit_pos:
                    violations.append(
                        f"'status' (pos {status_pos + 1}) debe estar antes de "
                        f"'{audit_col}' (pos {audit_pos + 1})"
                    )
                break  # Only need to check against the first audit column
    else:
        violations.append("Falta columna 'status' — ¿se incluyó SoftDeleteMixin?")

    # --- 4. table_status debe estar antes de status ---
    table_status_cols = [
        (i, c) for i, c in enumerate(columns)
        if c.endswith("_status") and c != STATUS_COLUMN
    ]
    if table_status_cols and STATUS_COLUMN in columns:
        status_pos = columns.index(STATUS_COLUMN)
        for ts_pos, ts_name in table_status_cols:
            if ts_pos > status_pos:
                violations.append(
                    f"'{ts_name}' (pos {ts_pos + 1}) debe estar ANTES de "
                    f"'status' (pos {status_pos + 1})"
                )

    # --- 5. Columnas de auditoría deben ser las últimas y en orden ---
    present_audit = [c for c in columns if c in AUDIT_COLUMNS]
    expected_audit = [c for c in AUDIT_COLUMNS if c in columns]

    if present_audit != expected_audit:
        violations.append(
            f"Columnas de auditoría en orden incorrecto. "
            f"Esperado: {expected_audit}, actual: {present_audit}"
        )

    if present_audit:
        first_audit_pos = columns.index(present_audit[0])
        trailing = columns[first_audit_pos:]
        non_audit_after = [c for c in trailing if c not in AUDIT_COLUMNS]
        if non_audit_after:
            violations.append(
                f"Columnas de dominio después de auditoría: {non_audit_after}. "
                f"Deben estar ANTES de las columnas de auditoría."
            )

    if len(present_audit) != len(AUDIT_COLUMNS):
        missing = set(AUDIT_COLUMNS) - set(present_audit)
        violations.append(
            f"Faltan columnas de auditoría: {missing} — ¿se incluyó AuditMixin?"
        )

    return violations


def validate_all_models() -> dict[str, list[str]]:
    """Valida todos los modelos registrados en Base.

    Retorna dict con {tablename: [violaciones]} solo para modelos con problemas.
    """
    results = {}
    for mapper in Base.registry.mappers:
        model = mapper.class_
        if hasattr(model, "__tablename__"):
            violations = validate_column_order(model)
            if violations:
                results[model.__tablename__] = violations
    return results


if __name__ == "__main__":
    # Ejecutable como: python -m app.shared.database.validators
    # Requiere que los modelos estén importados previamente
    print("Validando modelos registrados en Base...\n")
    results = validate_all_models()
    if not results:
        print("Todos los modelos cumplen con el estándar.")
    else:
        for table, violations in results.items():
            print(f"TABLA: {table}")
            for v in violations:
                print(f"  - {v}")
            print()
