# Estándar de Base de Datos

## Regla Principal

**Toda tabla DEBE seguir el orden de columnas estandarizado y usar los mixins provistos.** No se permite definir columnas de auditoría o soft-delete manualmente.

## Orden de Columnas

| Orden | Grupo | Columnas | Razón Técnica |
|-------|-------|----------|---------------|
| 1 | Identidad | `id` | Siempre al inicio para indexación rápida y legibilidad |
| 2 | Relaciones | `fk_*` | Agrupar FKs facilita la comprensión del esquema relacional |
| 3 | Dominio | `{datos}` | El core del negocio |
| 4 | Lógica de negocio | `{table_status}` | Estado de negocio (ej: `patient_status`, `appointment_status`) |
| 5 | Control técnico | `status` | Status del registro: **A** (active), **I** (inactive), **T** (trash) |
| 6 | Auditoría creación | `created_at`, `created_by` | Pareja: cuándo + quién creó |
| 7 | Auditoría edición | `updated_at`, `updated_by` | Pareja: cuándo + quién editó |
| 8 | Auditoría eliminación | `deleted_at`, `deleted_by` | Solo en recuperación — por eso van al final |

## Columna `status` — Soft Delete

El campo `status` es el **status técnico** del registro. Controla la visibilidad lógica:

| Valor | Nombre | Significado |
|-------|--------|-------------|
| `A` | Active | Registro vigente y visible en consultas normales |
| `I` | Inactive | Registro deshabilitado, no visible pero recuperable |
| `T` | Trash | Marcado para eliminación. Recuperable por administradores |

**Nunca** se hace `DELETE FROM` en producción. Siempre se cambia `status` a `T` y se llena `deleted_at` + `deleted_by`.

## Columna `{table_status}` — Status de Negocio

Es un status **de dominio**, diferente al status técnico. Ejemplos:

| Módulo | Columna | Valores posibles |
|--------|---------|------------------|
| `patients` | `patient_status` | `PRE-DIAGNOSIS`, `IN-TREATMENT`, `DISCHARGED` |
| `appointments` | `appointment_status` | `SCHEDULED`, `CONFIRMED`, `IN-PROGRESS`, `COMPLETED`, `CANCELLED` |
| `inventory` | `item_status` | `AVAILABLE`, `LOW-STOCK`, `OUT-OF-STOCK`, `EXPIRED` |

Cada módulo define su propio Enum para el `table_status`. **No confundir** con `status` (técnico).

## Auditoría — Parejas de Trazabilidad

Cada acción (crear, editar, eliminar) se registra con **timestamp + actor**:

| Acción | Timestamp | Actor | Se llena cuando... |
|--------|-----------|-------|---------------------|
| Crear | `created_at` | `created_by` | Se inserta el registro |
| Editar | `updated_at` | `updated_by` | Se modifica cualquier campo |
| Eliminar | `deleted_at` | `deleted_by` | Se cambia `status` a `T` |

- `created_at` tiene `server_default=func.now()` — se llena automáticamente.
- `updated_at` tiene `onupdate` — se actualiza automáticamente al modificar.
- `deleted_at` / `deleted_by` se llenan manualmente en el use case de soft-delete.
- `*_by` almacenan el UUID del usuario (String(36)), obtenido de `get_current_user_id()`.

## Cómo Crear un Modelo

### Imports necesarios

```python
from sqlalchemy import String, ForeignKey, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.database.base import Base
from app.shared.database.mixins import AuditMixin, SoftDeleteMixin
```

### Ejemplo completo: PatientModel

```python
# app/modules/patients/infrastructure/models.py
from typing import Optional

from sqlalchemy import Date, String
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.database.base import Base
from app.shared.database.mixins import AuditMixin, SoftDeleteMixin


class PatientModel(Base, SoftDeleteMixin, AuditMixin):
    __tablename__ = "patients"

    # --- Grupo 1: Identidad ---
    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # --- Grupo 2: Relaciones (este modelo no tiene FKs) ---

    # --- Grupo 3: Dominio ---
    first_name: Mapped[str] = mapped_column(String(255), nullable=False)
    last_name: Mapped[str] = mapped_column(String(255), nullable=False)
    cedula: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    date_of_birth: Mapped[Optional[str]] = mapped_column(Date, nullable=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # --- Grupo 4: Lógica de negocio ---
    patient_status: Mapped[Optional[str]] = mapped_column(
        String(30), nullable=True, default=None
    )

    # --- Grupos 5-8: Vienen de SoftDeleteMixin y AuditMixin ---
    # status, created_at, created_by, updated_at, updated_by, deleted_at, deleted_by
```

### Ejemplo con Foreign Keys: AppointmentModel

```python
# app/modules/appointments/infrastructure/models.py
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.database.base import Base
from app.shared.database.mixins import AuditMixin, SoftDeleteMixin


class AppointmentModel(Base, SoftDeleteMixin, AuditMixin):
    __tablename__ = "appointments"

    # --- Grupo 1: Identidad ---
    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # --- Grupo 2: Relaciones ---
    fk_patient_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("patients.id"), nullable=False, index=True
    )
    fk_doctor_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False, index=True
    )

    # --- Grupo 3: Dominio ---
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration_minutes: Mapped[int] = mapped_column(nullable=False, default=30)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # --- Grupo 4: Lógica de negocio ---
    appointment_status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="SCHEDULED"
    )

    # --- Grupos 5-8: Vienen de SoftDeleteMixin y AuditMixin ---
```

## Convención de Nombres

### Tablas
- Plural, snake_case: `patients`, `appointments`, `inventory_items`

### Columnas
- snake_case: `first_name`, `date_of_birth`
- Foreign keys con prefijo `fk_`: `fk_patient_id`, `fk_doctor_id`
- Table status con sufijo `_status`: `patient_status`, `appointment_status`

### Constraints (automático por naming convention)
- Primary key: `pk_patients`
- Foreign key: `fk_appointments_fk_patient_id_patients`
- Índice: `ix_patients_cedula`
- Unique: `uq_patients_cedula`

## Lo que NUNCA debes hacer

### 1. Definir columnas de auditoría manualmente

```python
# MAL — las define el AuditMixin
class PatientModel(Base, SoftDeleteMixin, AuditMixin):
    __tablename__ = "patients"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    created_at: Mapped[datetime] = ...  # DUPLICADO con AuditMixin

# BIEN — solo hereda el mixin
class PatientModel(Base, SoftDeleteMixin, AuditMixin):
    __tablename__ = "patients"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    # created_at viene del AuditMixin
```

### 2. Usar is_active en lugar de status

```python
# MAL
is_active: Mapped[bool] = mapped_column(Boolean, default=True)

# BIEN — el SoftDeleteMixin provee `status` con A/I/T
# No definir nada, el mixin lo agrega
```

### 3. Omitir los mixins

```python
# MAL — sin mixins
class PatientModel(Base):
    __tablename__ = "patients"
    id: Mapped[str] = ...

# BIEN — siempre incluir ambos mixins
class PatientModel(Base, SoftDeleteMixin, AuditMixin):
    __tablename__ = "patients"
    id: Mapped[str] = ...
```

### 4. FK sin prefijo fk_

```python
# MAL
patient_id: Mapped[str] = mapped_column(ForeignKey("patients.id"))

# BIEN
fk_patient_id: Mapped[str] = mapped_column(
    String(36), ForeignKey("patients.id"), nullable=False, index=True
)
```

### 5. Hacer DELETE en producción

```python
# MAL — hard delete
await session.delete(patient)

# BIEN — soft delete
patient.status = RecordStatus.TRASH
patient.deleted_at = datetime.now(timezone.utc)
patient.deleted_by = current_user_id
```

### 6. Confundir table_status con status

```python
# MAL — usar `status` para lógica de negocio
patient.status = "DISCHARGED"  # Esto es el status TÉCNICO (A/I/T)

# BIEN — usar la columna de dominio
patient.patient_status = "DISCHARGED"
patient.status = RecordStatus.ACTIVE  # Sigue activo técnicamente
```

## Migraciones

### Caso 1: Crear tabla nueva (CREATE TABLE)

Al crear una tabla nueva, el orden de columnas se respeta automáticamente gracias al MRO de Python:

1. Columnas del modelo (id, fk_*, datos, table_status) — en orden de definición
2. `status` — de `SoftDeleteMixin`
3. `created_at, created_by, updated_at, updated_by, deleted_at, deleted_by` — de `AuditMixin`

```bash
# 1. Crear el modelo en app/modules/{modulo}/infrastructure/models.py
# 2. Importar el modelo en alembic/env.py
# 3. Generar migración
alembic revision --autogenerate -m "add patients table"
# 4. REVISAR la migración generada (ver checklist abajo)
# 5. Aplicar
alembic upgrade head
```

**El orden es automático. No requiere intervención.**

### Caso 2: Agregar columnas a tabla existente (ALTER TABLE)

**Limitación de PostgreSQL:** `ADD COLUMN` siempre agrega la columna al **FINAL** de la tabla física. No existe `ADD COLUMN ... AFTER column_name` como en MySQL.

Esto significa que si agregas `email` y `phone` a `patients`, físicamente quedan DESPUÉS de `deleted_by`:

```
-- Orden FÍSICO en PostgreSQL (después del ALTER):
id, first_name, cedula, patient_status, status,
created_at, created_by, ..., deleted_by,
email, phone   ← al final, fuera de orden
```

#### ¿Afecta el rendimiento o las consultas? **NO.**

PostgreSQL almacena datos en heap tuples donde el orden físico no impacta rendimiento.
Las consultas siempre deben usar columnas explícitas (`SELECT id, first_name, ...`), nunca `SELECT *`.

#### Reglas para modificar tablas

| Regla | Qué hacer |
|-------|-----------|
| **Modelo Python** | SIEMPRE actualizar con la columna en su grupo correcto (es la fuente de verdad) |
| **Migración** | Usar `op.add_column()` normal — va al final físicamente, es aceptable |
| **Orden físico** | Solo reordenar si el DBA lo exige explícitamente (ver sección abajo) |

#### Paso a paso: agregar columna a tabla existente

```python
# 1. PRIMERO: actualizar el modelo con la columna en su grupo correcto

class PatientModel(Base, SoftDeleteMixin, AuditMixin):
    __tablename__ = "patients"

    # --- Grupo 1: Identidad ---
    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # --- Grupo 3: Dominio ---
    first_name: Mapped[str] = mapped_column(String(255), nullable=False)
    last_name: Mapped[str] = mapped_column(String(255), nullable=False)
    cedula: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)    # ← NUEVO, en su grupo
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)     # ← NUEVO, en su grupo

    # --- Grupo 4: Lógica de negocio ---
    patient_status: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)

    # --- Grupos 5-8: Mixins ---
```

```bash
# 2. Generar migración
alembic revision --autogenerate -m "add email and phone to patients"

# 3. Revisar la migración generada — será algo como:
#    op.add_column('patients', sa.Column('email', sa.String(255), nullable=True))
#    op.add_column('patients', sa.Column('phone', sa.String(20), nullable=True))
#    (se agregan al final físicamente, es correcto)

# 4. Aplicar
alembic upgrade head
```

```bash
# 5. Validar que el modelo mantiene el orden lógico
python -c "
from app.modules.patients.infrastructure.models import PatientModel
from app.shared.database.validators import validate_column_order
violations = validate_column_order(PatientModel)
print('OK' if not violations else violations)
"
```

### Caso 3: Reordenar columnas físicamente (solo si el DBA lo exige)

Si por requisito del DBA las columnas deben estar en orden físico correcto, se debe **recrear la tabla**:

```python
# alembic/versions/xxxx_reorder_patients_columns.py
"""reorder patients columns

Revision ID: xxxx
"""
from alembic import op
import sqlalchemy as sa

def upgrade() -> None:
    # ADVERTENCIA: Esto bloquea la tabla durante la operación.
    # Solo usar cuando el DBA lo requiera explícitamente.

    # 1. Crear tabla temporal con el orden correcto
    op.execute("""
        CREATE TABLE patients_new AS
        SELECT
            id,
            first_name, last_name, cedula, email, phone,
            patient_status,
            status,
            created_at, created_by,
            updated_at, updated_by,
            deleted_at, deleted_by
        FROM patients
    """)

    # 2. Eliminar tabla vieja
    op.execute("DROP TABLE patients CASCADE")

    # 3. Renombrar
    op.execute("ALTER TABLE patients_new RENAME TO patients")

    # 4. Recrear constraints
    op.execute("ALTER TABLE patients ADD PRIMARY KEY (id)")
    op.execute("CREATE UNIQUE INDEX uq_patients_cedula ON patients (cedula)")
    op.execute("CREATE INDEX ix_patients_status ON patients (status)")
    # ... recrear FKs, índices, etc.

def downgrade() -> None:
    # No es práctico revertir un reordenamiento
    pass
```

> **Importante:** Recrear tablas con datos en producción es una operación costosa y peligrosa. Solo hacerlo cuando sea estrictamente necesario y siempre en ventana de mantenimiento.

### Caso 4: Renombrar o eliminar columnas

```python
# Renombrar
def upgrade() -> None:
    op.alter_column("patients", "old_name", new_column_name="new_name")

# Eliminar (SOLO columnas de dominio, NUNCA de auditoría)
def upgrade() -> None:
    op.drop_column("patients", "column_to_remove")
```

**NUNCA** eliminar ni renombrar: `id`, `status`, `created_at`, `created_by`, `updated_at`, `updated_by`, `deleted_at`, `deleted_by`.

### Checklist de revisión de migraciones

Antes de hacer push, verificar:

**Para CREATE TABLE:**
- [ ] `id` como PK con `String(36)`
- [ ] Todas las FKs con prefijo `fk_`
- [ ] Columnas de dominio en el grupo correcto
- [ ] `table_status` antes de `status` (si aplica)
- [ ] `status` con enum `record_status` y default `'A'`
- [ ] `created_at` con `server_default=sa.func.now()`
- [ ] `created_by`, `updated_at`, `updated_by`, `deleted_at`, `deleted_by` presentes
- [ ] Constraints con nombres del naming convention
- [ ] `downgrade()` que revierta correctamente

**Para ALTER TABLE (agregar columnas):**
- [ ] Modelo Python actualizado con la columna en su grupo correcto
- [ ] Migración usa `op.add_column()` (no construir SQL manual)
- [ ] `downgrade()` con `op.drop_column()` correspondiente
- [ ] Si la columna es NOT NULL, proveer `server_default` para datos existentes
- [ ] Ejecutar validador de orden: `python -m app.shared.database.validators`

## Validador de Orden

El proyecto incluye un validador automático en `app/shared/database/validators.py`:

```python
# En un test
from app.shared.database.validators import validate_column_order
from app.modules.patients.infrastructure.models import PatientModel

def test_patient_column_order():
    violations = validate_column_order(PatientModel)
    assert violations == [], f"Violaciones: {violations}"
```

```bash
# Como script (valida TODOS los modelos registrados)
python -m app.shared.database.validators
```

El validador verifica:
- `id` es la primera columna
- FKs (`fk_*`) están justo después de `id`
- `table_status` está antes de `status`
- `status` está antes de columnas de auditoría
- Columnas de auditoría están al final y en el orden correcto de parejas
- No faltan columnas de los mixins

## Resumen Rápido

| Necesito... | Usar... |
|-------------|---------|
| Soft delete | `SoftDeleteMixin` → columna `status` (A/I/T) |
| Auditoría completa | `AuditMixin` → 6 columnas pareadas |
| Status de dominio | Columna propia `{table}_status` con Enum del módulo |
| FK | `fk_{tabla_ref}_id` con `ForeignKey` e `index=True` |
| ID | `String(36)` con `primary_key=True` (UUID) |
| Eliminar registro | Cambiar `status=T` + llenar `deleted_at/by` |
| Crear tabla nueva | Autogenerate → orden automático correcto |
| Agregar columna | `op.add_column()` + modelo en orden lógico |
| Reordenar físicamente | Recrear tabla (solo si DBA lo exige) |
| Validar orden | `python -m app.shared.database.validators` |
