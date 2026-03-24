# Estándar de Eficiencia y Rendimiento

## Contexto

Este sistema se despliega en **equipos de escasos recursos**. Cada decisión de diseño debe priorizar eficiencia computacional. Los jurados evaluarán análisis de complejidad algorítmica (Big O) y uso eficiente de recursos.

## Complejidad Algorítmica — Reglas

### Complejidades aceptables por operación

| Operación | Máximo aceptable | Ejemplo |
|-----------|-------------------|---------|
| Búsqueda por ID/PK | **O(1)** | `SELECT ... WHERE id = ?` con índice |
| Búsqueda por campo indexado | **O(log n)** | `SELECT ... WHERE cedula = ?` con índice B-tree |
| Listado paginado | **O(log n + k)** | `SELECT ... LIMIT k OFFSET ...` con índice, k = page_size |
| Filtrado con WHERE | **O(log n)** | Solo si el campo tiene índice |
| Creación de registro | **O(1)** amortizado | INSERT con UUID pre-generado |
| Actualización por ID | **O(1)** | UPDATE ... WHERE id = ? |
| Soft-delete por ID | **O(1)** | UPDATE status = 'T' WHERE id = ? |
| Búsqueda full-text | **O(n)** solo si no hay alternativa | Considerar `pg_trgm` o `tsvector` |

### Complejidades PROHIBIDAS

| Complejidad | Ejemplo | Por qué es inaceptable |
|-------------|---------|------------------------|
| **O(n²)** | Loop anidado sobre resultados de BD | Con 10,000 registros = 100 millones de operaciones |
| **O(n × m)** | Por cada paciente, consultar todas sus citas sin JOIN | N+1 queries, satura conexiones |
| **O(2ⁿ)** | Algoritmos de fuerza bruta | Crece exponencialmente, inaceptable |
| **O(n!)** | Permutaciones | Inviable incluso con n pequeño |

## Reglas de Código

### R01: Prohibido el problema N+1

El error más común y más costoso en aplicaciones con ORM.

```python
# MAL — O(n) queries: 1 para pacientes + 1 por cada paciente para citas
# Si hay 1000 pacientes = 1001 queries
patients = await session.execute(select(PatientModel))
for patient in patients.scalars():
    appointments = await session.execute(
        select(AppointmentModel).where(
            AppointmentModel.fk_patient_id == patient.id
        )
    )

# BIEN — O(1) queries: un solo JOIN o subquery
# Siempre constante sin importar cuántos pacientes haya
from sqlalchemy.orm import selectinload

stmt = select(PatientModel).options(
    selectinload(PatientModel.appointments)
)
patients = await session.execute(stmt)
```

**Cuándo usar cada estrategia de carga:**

| Estrategia | Complejidad | Usar cuando... |
|------------|-------------|----------------|
| `selectinload` | O(2) queries | Relación 1-a-muchos, pocos hijos por padre |
| `joinedload` | O(1) query | Relación 1-a-1 o muchos-a-1 |
| `lazyload` | O(n) queries | **NUNCA** en producción, solo debugging |
| `subqueryload` | O(2) queries | Relación 1-a-muchos con filtros complejos |

### R02: Toda consulta de listado DEBE ser paginada

```python
# MAL — O(n) memoria: carga TODOS los registros en RAM
# Con 100,000 pacientes = cientos de MB en memoria
patients = await session.execute(select(PatientModel))
all_patients = patients.scalars().all()

# BIEN — O(k) memoria: k = page_size, constante y predecible
stmt = (
    select(PatientModel)
    .where(PatientModel.status == RecordStatus.ACTIVE)
    .order_by(PatientModel.created_at.desc())
    .offset((page - 1) * page_size)
    .limit(page_size)
)
patients = await session.execute(stmt)
```

**Límites obligatorios:**

| Parámetro | Default | Máximo | Razón |
|-----------|---------|--------|-------|
| `page_size` | 20 | 100 | Limitar payload y memoria |
| `page` | 1 | — | Offset-based pagination |

```python
# Validación obligatoria en el endpoint
from fastapi import Query

@router.get("/patients")
async def list_patients(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    ...
```

### R03: Índices en columnas de búsqueda y filtrado

Si una columna aparece en `WHERE`, `ORDER BY` o `JOIN`, **DEBE tener índice**.

```python
# Columnas que SIEMPRE necesitan índice:
id: Mapped[str] = mapped_column(String(36), primary_key=True)      # PK = índice auto
cedula: Mapped[str] = mapped_column(String(20), unique=True, index=True)  # búsqueda frecuente
fk_patient_id: Mapped[str] = mapped_column(
    String(36), ForeignKey("patients.id"), index=True               # JOIN frecuente
)
status: Mapped[str] = mapped_column(..., index=True)                # filtro en TODAS las queries

# Índices compuestos para queries frecuentes:
from sqlalchemy import Index

class AppointmentModel(Base, SoftDeleteMixin, AuditMixin):
    __tablename__ = "appointments"
    __table_args__ = (
        # Query frecuente: "citas activas de un doctor ordenadas por fecha"
        Index("ix_appointments_doctor_status_date",
              "fk_doctor_id", "status", "scheduled_at"),
    )
```

**Complejidad con y sin índice:**

| Operación | Sin índice | Con índice B-tree |
|-----------|-----------|-------------------|
| `WHERE id = ?` | O(n) scan | O(log n) seek |
| `WHERE status = 'A'` | O(n) scan | O(log n + k) |
| `ORDER BY created_at` | O(n log n) sort | O(n) index scan |
| `WHERE fk_id = ? AND status = ?` | O(n) scan | O(log n) con índice compuesto |

### R04: SELECT solo las columnas necesarias

```python
# MAL — O(n × cols) transferencia: trae TODAS las columnas incluyendo auditoría
# En tabla con 15 columnas, transfiere 15× más datos de los necesarios
stmt = select(PatientModel)

# BIEN — O(n × k) transferencia: k = columnas necesarias, k << cols
# Solo trae lo que el endpoint necesita
stmt = select(
    PatientModel.id,
    PatientModel.first_name,
    PatientModel.last_name,
    PatientModel.cedula,
)
```

**Cuándo aplicar:**
- Listados → SIEMPRE usar select parcial (menos datos por fila × muchas filas)
- Detalle por ID → aceptable traer todo el modelo (1 fila)
- Reportes → SIEMPRE select parcial + agregaciones en BD

### R05: Operaciones en lote, no individuales

```python
# MAL — O(n) roundtrips a BD: un INSERT por registro
# 1000 registros = 1000 queries = segundos de espera
for item in items:
    model = InventoryItemModel(**item)
    session.add(model)
    await session.flush()      # flush individual = roundtrip

# BIEN — O(1) roundtrips: un solo INSERT masivo
# 1000 registros = 1 query = milisegundos
models = [InventoryItemModel(**item) for item in items]
session.add_all(models)
await session.flush()          # un solo flush = un roundtrip
```

### R06: Contar registros eficientemente

```python
from sqlalchemy import func

# MAL — O(n) memoria: carga todos los registros para contarlos
all_items = await session.execute(select(PatientModel))
total = len(all_items.scalars().all())

# BIEN — O(log n) con índice: cuenta en BD, transfiere solo un número
result = await session.execute(
    select(func.count()).select_from(PatientModel).where(
        PatientModel.status == RecordStatus.ACTIVE
    )
)
total = result.scalar_one()
```

### R07: Filtrar soft-deleted en BD, no en Python

```python
# MAL — O(n) memoria + O(n) filtrado: carga TODO y filtra en Python
all_patients = await session.execute(select(PatientModel))
active = [p for p in all_patients.scalars() if p.status == "A"]

# BIEN — O(log n) con índice: filtra en BD, transfiere solo activos
stmt = select(PatientModel).where(
    PatientModel.status == RecordStatus.ACTIVE
)
active = await session.execute(stmt)
```

### R08: No computar en Python lo que la BD puede hacer

```python
# MAL — O(n) transferencia + O(n) cómputo en Python
result = await session.execute(select(AppointmentModel))
appointments = result.scalars().all()
count_by_status = {}
for apt in appointments:
    count_by_status[apt.appointment_status] = count_by_status.get(apt.appointment_status, 0) + 1

# BIEN — O(grupos) transferencia: GROUP BY en BD
from sqlalchemy import func

stmt = (
    select(
        AppointmentModel.appointment_status,
        func.count().label("total"),
    )
    .where(AppointmentModel.status == RecordStatus.ACTIVE)
    .group_by(AppointmentModel.appointment_status)
)
result = await session.execute(stmt)
```

### R09: Usar generadores para procesamiento de datos grandes

```python
# MAL — O(n) memoria: materializa lista completa
def process_all(items: list) -> list:
    results = []
    for item in items:
        results.append(transform(item))
    return results

# BIEN — O(1) memoria: genera uno a la vez
def process_all(items: list):
    for item in items:
        yield transform(item)

# MEJOR — para SQLAlchemy, usar yield_per para grandes datasets
stmt = select(PatientModel).execution_options(yield_per=100)
result = await session.stream(stmt)
async for patient in result.scalars():
    # Procesa de 100 en 100, no carga todo en RAM
    ...
```

### R10: Async sin bloqueo

```python
import asyncio

# MAL — bloquea el event loop, mata la concurrencia
import time
time.sleep(5)  # Bloquea TODO el servidor durante 5 segundos

# BIEN — no bloquea
await asyncio.sleep(5)

# MAL — operación CPU-intensiva en el event loop
result = heavy_computation(data)  # Bloquea mientras computa

# BIEN — delegar a thread pool
result = await asyncio.get_event_loop().run_in_executor(
    None, heavy_computation, data
)
```

## Métricas de Rendimiento — Presupuestos

Para equipos de escasos recursos, cada endpoint tiene un presupuesto de tiempo:

| Tipo de endpoint | Tiempo máximo | Queries máximas |
|-----------------|---------------|-----------------|
| GET por ID | 50ms | 1-2 |
| GET listado paginado | 100ms | 2-3 (count + select) |
| POST crear | 100ms | 1-2 (check + insert) |
| PUT/PATCH actualizar | 100ms | 2 (select + update) |
| DELETE (soft) | 50ms | 1 (update) |
| Reportes/agregaciones | 500ms | 1-3 (queries con GROUP BY) |

## Pool de Conexiones — Configuración

Configurado en `app/core/config.py` y `app/shared/database/session.py`:

```
DB_POOL_SIZE=5          # Conexiones persistentes (bajo para ahorrar RAM)
DB_MAX_OVERFLOW=3       # Conexiones extras en picos (total máximo: 8)
DB_POOL_RECYCLE=1800    # Reciclar cada 30min para evitar leaks
pool_pre_ping=True      # Verificar conexión viva antes de usar
```

**Por qué estos valores:**
- Cada conexión PostgreSQL consume ~5-10 MB de RAM en el servidor
- Con pool_size=5 y max_overflow=3: máximo 8 conexiones = ~80 MB
- En equipos con 2-4 GB RAM, esto deja espacio para la aplicación

## Patrones Prohibidos — Resumen

| Patrón | Complejidad | Alternativa | Complejidad |
|--------|-------------|-------------|-------------|
| Loop + query individual | O(n) queries | JOIN / selectinload | O(1-2) queries |
| `select(Model)` sin LIMIT | O(n) memoria | `.limit(page_size)` | O(k) memoria |
| `len(query.all())` | O(n) memoria | `func.count()` | O(log n) |
| Filtrar en Python | O(n) transferencia | WHERE en SQL | O(log n) |
| GROUP BY en Python | O(n) transferencia | GROUP BY en SQL | O(n) en BD, O(k) transferencia |
| `session.flush()` en loop | O(n) roundtrips | `add_all()` + 1 flush | O(1) roundtrip |
| `SELECT *` en listados | O(n × cols) datos | Select parcial | O(n × k) datos |
| `time.sleep()` | Bloquea event loop | `asyncio.sleep()` | No bloquea |
| Sin índice en WHERE | O(n) scan | Índice B-tree | O(log n) |

## Checklist de Eficiencia — Antes de hacer PR

- [ ] ¿Todo listado está paginado con `page_size` máximo de 100?
- [ ] ¿Las consultas usan `selectinload`/`joinedload` en vez de queries en loop?
- [ ] ¿Las columnas de filtro/JOIN tienen índice?
- [ ] ¿Los listados hacen select parcial (solo columnas necesarias)?
- [ ] ¿Las operaciones masivas usan `add_all()` en vez de `add()` en loop?
- [ ] ¿Los conteos usan `func.count()` en vez de `len(.all())`?
- [ ] ¿Los filtros están en SQL (WHERE), no en Python?
- [ ] ¿No hay `time.sleep()` ni operaciones bloqueantes en el event loop?
- [ ] ¿Puedo justificar la complejidad Big O de cada operación del endpoint?
