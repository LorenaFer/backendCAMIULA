# Guía de Commits — Feature NHM Endpoints

> **Branch:** `feature/nhm-endpoints` → PR a `main`
> **Convención:** `<tipo>(<scope>): <descripción imperativa en español>`
> **Tipos:** `feat`, `fix`, `refactor`, `test`, `chore`, `docs`

Cada commit debe compilar sin errores y no romper los tests existentes. Sigue el orden listado: dominio → aplicación → infraestructura → presentación → wiring → tests → docs.

---

## Commits de Implementación (orden obligatorio)

### Commit 1 — Dominio: entidad Specialty con soporte CRUD

**Archivos:**
```
app/modules/appointments/domain/entities/specialty.py
app/modules/appointments/domain/repositories/specialty_repository.py
```

**Qué incluye:**
- Campo `is_active: bool = True` en entidad `Specialty`
- Repositorio ABC con métodos: `get_by_name`, `create`, `update`, `toggle`

```bash
git add app/modules/appointments/domain/entities/specialty.py \
        app/modules/appointments/domain/repositories/specialty_repository.py
git commit -m "feat(domain): agregar campos CRUD a entidad Specialty"
```

---

### Commit 2 — Dominio: campos schema en MedicalRecord + método historial

**Archivos:**
```
app/modules/appointments/domain/entities/medical_record.py
app/modules/appointments/domain/repositories/medical_record_repository.py
```

**Qué incluye:**
- Campos opcionales `schema_id` y `schema_version` en entidad `MedicalRecord`
- Método abstracto `get_patient_history(patient_id, limit, exclude_appointment_id)` en repositorio ABC

```bash
git add app/modules/appointments/domain/entities/medical_record.py \
        app/modules/appointments/domain/repositories/medical_record_repository.py
git commit -m "feat(domain): agregar schema_id/schema_version a MedicalRecord y método get_patient_history"
```

---

### Commit 3 — Dominio: método get_stats en AppointmentRepository

**Archivos:**
```
app/modules/appointments/domain/repositories/appointment_repository.py
```

**Qué incluye:**
- Método abstracto `get_stats(fecha, doctor_id, specialty_id) -> Dict[str, Any]`

```bash
git add app/modules/appointments/domain/repositories/appointment_repository.py
git commit -m "feat(domain): agregar método get_stats al repositorio de citas"
```

---

### Commit 4 — Application: DTO MedicalRecord actualizado

**Archivos:**
```
app/modules/appointments/application/dtos/medical_record_dto.py
app/modules/appointments/application/use_cases/upsert_medical_record.py
```

**Qué incluye:**
- Campos opcionales `schema_id` y `schema_version` en `UpsertMedicalRecordDTO`
- `UpsertMedicalRecordUseCase` actualizado para pasar los nuevos campos

```bash
git add app/modules/appointments/application/dtos/medical_record_dto.py \
        app/modules/appointments/application/use_cases/upsert_medical_record.py
git commit -m "feat(appointments): agregar schema_id y schema_version al DTO de historia médica"
```

---

### Commit 5 — Application: casos de uso CRUD de especialidades

**Archivos:**
```
app/modules/appointments/application/use_cases/create_specialty.py
app/modules/appointments/application/use_cases/update_specialty.py
app/modules/appointments/application/use_cases/toggle_specialty.py
```

**Qué incluye:**
- `CreateSpecialtyUseCase` — verifica nombre único, lanza 409 si duplicado
- `UpdateSpecialtyUseCase` — verifica existencia (404) y nombre no duplicado (409)
- `ToggleSpecialtyUseCase` — verifica existencia (404), delega toggle al repositorio

```bash
git add app/modules/appointments/application/use_cases/create_specialty.py \
        app/modules/appointments/application/use_cases/update_specialty.py \
        app/modules/appointments/application/use_cases/toggle_specialty.py
git commit -m "feat(appointments): implementar casos de uso para CRUD de especialidades"
```

---

### Commit 6 — Application: casos de uso de stats y historial

**Archivos:**
```
app/modules/appointments/application/use_cases/get_appointment_stats.py
app/modules/appointments/application/use_cases/get_patient_medical_history.py
```

**Qué incluye:**
- `GetAppointmentStatsUseCase` — delega a `repo.get_stats()` con filtros opcionales
- `GetPatientMedicalHistoryUseCase` — delega a `repo.get_patient_history()` con limit y exclusión

```bash
git add app/modules/appointments/application/use_cases/get_appointment_stats.py \
        app/modules/appointments/application/use_cases/get_patient_medical_history.py
git commit -m "feat(appointments): implementar casos de uso para estadísticas y historial de paciente"
```

---

### Commit 7 — Infrastructure: modelo SQLAlchemy con columnas de schema

**Archivos:**
```
app/modules/appointments/infrastructure/models.py
```

**Qué incluye:**
- `schema_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)`
- `schema_version: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)`

```bash
git add app/modules/appointments/infrastructure/models.py
git commit -m "feat(appointments): agregar columnas schema_id y schema_version al modelo MedicalRecord"
```

---

### Commit 8 — Infrastructure: repositorio Specialty con métodos CRUD

**Archivos:**
```
app/modules/appointments/infrastructure/repositories/sqlalchemy_specialty_repository.py
```

**Qué incluye:**
- Métodos `get_by_name`, `create`, `update`, `toggle`
- `_to_entity` con `is_active = (model.status == RecordStatus.ACTIVE)`

```bash
git add app/modules/appointments/infrastructure/repositories/sqlalchemy_specialty_repository.py
git commit -m "feat(appointments): implementar métodos CRUD en SQLAlchemySpecialtyRepository"
```

---

### Commit 9 — Infrastructure: repositorio Appointment con get_stats

**Archivos:**
```
app/modules/appointments/infrastructure/repositories/sqlalchemy_appointment_repository.py
```

**Qué incluye:**
- `get_stats()` con consultas de agregación: by-status, by-specialty, by-doctor, first-time vs returning, by-patient-type, peak-hours
- Uso de `case()` de SQLAlchemy para conteos condicionales

```bash
git add app/modules/appointments/infrastructure/repositories/sqlalchemy_appointment_repository.py
git commit -m "feat(appointments): implementar get_stats con agregaciones en SQLAlchemyAppointmentRepository"
```

---

### Commit 10 — Infrastructure: repositorio MedicalRecord actualizado

**Archivos:**
```
app/modules/appointments/infrastructure/repositories/sqlalchemy_medical_record_repository.py
```

**Qué incluye:**
- `get_patient_history()` — historial del paciente con límite y exclusión de cita actual
- `upsert()` y `_to_entity()` actualizados para `schema_id` / `schema_version`

```bash
git add app/modules/appointments/infrastructure/repositories/sqlalchemy_medical_record_repository.py
git commit -m "feat(appointments): actualizar SQLAlchemyMedicalRecordRepository con schema_id y get_patient_history"
```

---

### Commit 11 — Presentation: schemas y rutas CRUD de especialidades

**Archivos:**
```
app/modules/appointments/presentation/schemas/doctor_schema.py
app/modules/appointments/presentation/routes/doctor_routes.py
```

**Qué incluye:**
- Schemas `SpecialtyCreateRequest`, `SpecialtyUpdateRequest`
- Rutas: `POST /specialties`, `PUT /specialties/{id}`, `PATCH /specialties/{id}/toggle`
- Permiso requerido: `doctors:write`
- `GET /specialties` actualizado: ahora retorna campo `activo` en cada especialidad

```bash
git add app/modules/appointments/presentation/schemas/doctor_schema.py \
        app/modules/appointments/presentation/routes/doctor_routes.py
git commit -m "feat(appointments): agregar endpoints POST/PUT/PATCH para especialidades"
```

---

### Commit 12 — Presentation: endpoint GET /appointments/stats

**Archivos:**
```
app/modules/appointments/presentation/schemas/appointment_schema.py
app/modules/appointments/presentation/routes/appointment_routes.py
```

**Qué incluye:**
- Schema `AppointmentStatsResponse`
- Ruta `GET /appointments/stats` registrada **ANTES** de `GET /{appointment_id}` para evitar conflicto de path (FastAPI usa el primer match)
- Filtros opcionales: `fecha`, `doctor_id`, `especialidad_id`

> **Importante:** el orden de las rutas importa. `GET /stats` debe quedar antes de `GET /{appointment_id}` en el archivo, o FastAPI tratará "stats" como un `appointment_id`.

```bash
git add app/modules/appointments/presentation/schemas/appointment_schema.py \
        app/modules/appointments/presentation/routes/appointment_routes.py
git commit -m "feat(appointments): agregar endpoint de estadísticas GET /appointments/stats"
```

---

### Commit 13 — Presentation: rutas y schemas de historias médicas

**Archivos:**
```
app/modules/appointments/presentation/schemas/medical_record_schema.py
app/modules/appointments/presentation/routes/medical_record_routes.py
```

**Qué incluye:**
- `schema_id` / `schema_version` en `UpsertMedicalRecordRequest` y `MedicalRecordResponse`
- Clase `PatientHistoryEntry`
- Ruta `GET /medical-records/patient/{patient_id}` con parámetros `limit` y `exclude`

```bash
git add app/modules/appointments/presentation/schemas/medical_record_schema.py \
        app/modules/appointments/presentation/routes/medical_record_routes.py
git commit -m "feat(appointments): agregar endpoint GET /medical-records/patient/{id} y campos de schema"
```

---

### Commit 14 — Módulo form_schemas: dominio

**Archivos:**
```
app/modules/form_schemas/__init__.py
app/modules/form_schemas/domain/__init__.py
app/modules/form_schemas/domain/entities/__init__.py
app/modules/form_schemas/domain/entities/form_schema.py
app/modules/form_schemas/domain/repositories/__init__.py
app/modules/form_schemas/domain/repositories/form_schema_repository.py
```

**Qué incluye:**
- Entidad `FormSchema` con PK semántico (`"medicina-general-v1"`)
- `normalize_name()` — NFD decomposition, strip accents, lowercase, espacios→guiones
- `validate()` — verifica que `schema_json` contenga `"sections"` como lista
- ABC `FormSchemaRepository` con: `list_all`, `get_by_id`, `get_by_specialty_id_or_key`, `upsert`, `delete`

```bash
git add app/modules/form_schemas/__init__.py \
        app/modules/form_schemas/domain/__init__.py \
        app/modules/form_schemas/domain/entities/__init__.py \
        app/modules/form_schemas/domain/entities/form_schema.py \
        app/modules/form_schemas/domain/repositories/__init__.py \
        app/modules/form_schemas/domain/repositories/form_schema_repository.py
git commit -m "feat(form-schemas): implementar entidad FormSchema con normalización de nombre"
```

---

### Commit 15 — Módulo form_schemas: capa de aplicación

**Archivos:**
```
app/modules/form_schemas/application/__init__.py
app/modules/form_schemas/application/dtos/__init__.py
app/modules/form_schemas/application/dtos/form_schema_dto.py
app/modules/form_schemas/application/use_cases/__init__.py
app/modules/form_schemas/application/use_cases/list_form_schemas.py
app/modules/form_schemas/application/use_cases/get_form_schema.py
app/modules/form_schemas/application/use_cases/upsert_form_schema.py
app/modules/form_schemas/application/use_cases/delete_form_schema.py
```

**Qué incluye:**
- `UpsertFormSchemaDTO` (frozen dataclass)
- `ListFormSchemasUseCase`
- `GetFormSchemaUseCase` — fallback a `"medicina-general"` si no existe schema
- `UpsertFormSchemaUseCase` — llama `schema.validate()`, lanza `AppException(422)` si falla
- `DeleteFormSchemaUseCase` — lanza 404 si no existe

```bash
git add app/modules/form_schemas/application/__init__.py \
        app/modules/form_schemas/application/dtos/__init__.py \
        app/modules/form_schemas/application/dtos/form_schema_dto.py \
        app/modules/form_schemas/application/use_cases/__init__.py \
        app/modules/form_schemas/application/use_cases/list_form_schemas.py \
        app/modules/form_schemas/application/use_cases/get_form_schema.py \
        app/modules/form_schemas/application/use_cases/upsert_form_schema.py \
        app/modules/form_schemas/application/use_cases/delete_form_schema.py
git commit -m "feat(form-schemas): implementar DTOs y casos de uso para form schemas"
```

---

### Commit 16 — Módulo form_schemas: infraestructura

**Archivos:**
```
app/modules/form_schemas/infrastructure/__init__.py
app/modules/form_schemas/infrastructure/models.py
app/modules/form_schemas/infrastructure/repositories/__init__.py
app/modules/form_schemas/infrastructure/repositories/sqlalchemy_form_schema_repository.py
```

**Qué incluye:**
- `FormSchemaModel(Base, SoftDeleteMixin, AuditMixin)` — cumple estándar de auditoría del proyecto
- PK `id: String(100)` (semántico, no UUID)
- Columna `schema_json: JSONB`
- Upsert por PK semántico, **soft-delete** (status → T)
- Campos de auditoría: `status`, `created_by`, `updated_by`, `deleted_at`, `deleted_by` vienen de los mixins

```bash
git add app/modules/form_schemas/infrastructure/__init__.py \
        app/modules/form_schemas/infrastructure/models.py \
        app/modules/form_schemas/infrastructure/repositories/__init__.py \
        app/modules/form_schemas/infrastructure/repositories/sqlalchemy_form_schema_repository.py
git commit -m "feat(form-schemas): implementar modelo SQLAlchemy y repositorio para form schemas"
```

---

### Commit 17 — Módulo form_schemas: presentación y router

**Archivos:**
```
app/modules/form_schemas/presentation/__init__.py
app/modules/form_schemas/presentation/schemas/__init__.py
app/modules/form_schemas/presentation/schemas/form_schema_schema.py
app/modules/form_schemas/presentation/routes/__init__.py
app/modules/form_schemas/presentation/routes/form_schema_routes.py
app/modules/form_schemas/router.py
```

**Qué incluye:**
- `UpsertFormSchemaRequest` con validación de `sections`
- 4 rutas: `GET /schemas`, `GET /schemas/{key}`, `PUT /schemas`, `DELETE /schemas/{id}`
- `_to_response()` — expande `schema_json` + agrega timestamps ISO
- Permisos: `schemas:read` / `schemas:write`

```bash
git add app/modules/form_schemas/presentation/__init__.py \
        app/modules/form_schemas/presentation/schemas/__init__.py \
        app/modules/form_schemas/presentation/schemas/form_schema_schema.py \
        app/modules/form_schemas/presentation/routes/__init__.py \
        app/modules/form_schemas/presentation/routes/form_schema_routes.py \
        app/modules/form_schemas/router.py
git commit -m "feat(form-schemas): agregar rutas y schemas de presentación para form schemas"
```

---

### Commit 18 — Migración Alembic

**Archivos:**
```
alembic/versions/a3f2e1b4c5d6_add_form_schemas_and_medical_record_schema_fields.py
alembic/env.py
```

**Qué incluye:**
- Creación tabla `form_schemas` con columnas en orden estándar:
  - Identidad: `id String(100)` (PK semántico)
  - Dominio: `specialty_id`, `specialty_name`, `version`, `schema_json JSONB`
  - Control: `status Enum(A/I/T) default 'A'`
  - Auditoría: `created_at`, `created_by`, `updated_at`, `updated_by`, `deleted_at`, `deleted_by`
- `ALTER TABLE medical_records ADD COLUMN schema_id VARCHAR(100)`
- `ALTER TABLE medical_records ADD COLUMN schema_version VARCHAR(20)`
- Índices: `ix_form_schemas_specialty_id`, `ix_form_schemas_status`
- `downgrade()` revierte ambos cambios

```bash
git add alembic/versions/a3f2e1b4c5d6_add_form_schemas_and_medical_record_schema_fields.py \
        alembic/env.py
git commit -m "chore(migrations): agregar tabla form_schemas con auditoría completa y campos schema en medical_records"
```

---

### Commit 19 — Wiring: registrar módulo form_schemas en main.py

**Archivos:**
```
app/main.py
```

**Qué incluye:**
- `from app.modules.form_schemas.router import router as form_schemas_router`
- `app.include_router(form_schemas_router, prefix="/api")`

```bash
git add app/main.py
git commit -m "chore(app): registrar router de form_schemas en main.py"
```

---

## Commits de Tests

Los commits de tests pueden ir intercalados inmediatamente después de sus respectivos módulos, o al final como bloque.

### Commit 20 — Tests: CRUD de especialidades

**Archivos:**
```
tests/unit/appointments/test_specialty_crud.py
```

Tests cubiertos: `CreateSpecialtyUseCase` (éxito, 409 duplicado), `UpdateSpecialtyUseCase` (éxito, 404, 409), `ToggleSpecialtyUseCase` (éxito, 404).

```bash
git add tests/unit/appointments/test_specialty_crud.py
git commit -m "test(appointments): agregar tests unitarios para casos de uso de especialidades"
```

---

### Commit 21 — Tests: estadísticas de citas

**Archivos:**
```
tests/unit/appointments/test_appointment_stats.py
```

Tests cubiertos: retorna estructura completa, pasa filtros correctamente al repositorio.

```bash
git add tests/unit/appointments/test_appointment_stats.py
git commit -m "test(appointments): agregar tests unitarios para GetAppointmentStatsUseCase"
```

---

### Commit 22 — Tests: historial médico del paciente

**Archivos:**
```
tests/unit/appointments/test_patient_history.py
```

Tests cubiertos: lista con límite y exclusión, lista vacía.

```bash
git add tests/unit/appointments/test_patient_history.py
git commit -m "test(appointments): agregar tests unitarios para GetPatientMedicalHistoryUseCase"
```

---

### Commit 23 — Tests: módulo form_schemas

**Archivos:**
```
tests/unit/form_schemas/__init__.py
tests/unit/form_schemas/test_entities.py
tests/unit/form_schemas/test_use_cases.py
```

Tests cubiertos: `FormSchema` (creación, `normalize_name`, `validate`), `ListFormSchemasUseCase`, `GetFormSchemaUseCase` (con y sin fallback), `UpsertFormSchemaUseCase` (éxito, 422), `DeleteFormSchemaUseCase` (éxito, 404).

> **Nota:** el test de `test_deletes_schema` verifica `repo.delete.assert_called_once_with("medicina-general-v1", deleted_by=None)` — incluir el argumento keyword en la aserción.

```bash
git add tests/unit/form_schemas/__init__.py \
        tests/unit/form_schemas/test_entities.py \
        tests/unit/form_schemas/test_use_cases.py
git commit -m "test(form-schemas): agregar tests unitarios para entidad FormSchema y casos de uso"
```

---

### Commit 24 — Seeder: schemas de formularios

**Archivos:**
```
app/modules/form_schemas/infrastructure/seeders/__init__.py
app/modules/form_schemas/infrastructure/seeders/form_schema_seeder.py
```

**Qué incluye:**
- `FormSchemaSeeder` (order=50, idempotente por id)
- 4 schemas iniciales: `medicina-general-v1`, `odontologia-v1`, `psicologia-v1`, `nutricion-v1`
- Cada schema tiene secciones con campos relevantes para CAMIULA
- `created_by = SYSTEM_USER_ID` (`00000000-0000-0000-0000-000000000000`)

```bash
git add app/modules/form_schemas/infrastructure/seeders/__init__.py \
        app/modules/form_schemas/infrastructure/seeders/form_schema_seeder.py
git commit -m "feat(form-schemas): agregar seeder con schemas iniciales para CAMIULA"
```

---

## Commit de Documentación

### Commit 25 — Documentación

**Archivos:**
```
docs/NHM_ENDPOINTS.md
docs/COMMIT_GUIDE.md
docs/09-endpoints-nhm-implementados.md
docs/10-guia-commits-nhm.md
```

```bash
git add docs/NHM_ENDPOINTS.md \
        docs/COMMIT_GUIDE.md \
        docs/09-endpoints-nhm-implementados.md \
        docs/10-guia-commits-nhm.md
git commit -m "docs: agregar documentación de endpoints NHM y guía de commits"
```

---

### Commit 26 — Script de integración NHM

**Archivos:**
```
scripts/test_nhm_endpoints.sh
```

**Qué incluye:**
- Verifica que PostgreSQL esté corriendo (`pg_isready`)
- Ejecuta migraciones Alembic y seeders antes de cada run
- Inserta automáticamente los permisos nuevos (`doctors:write`, `schemas:read`, `schemas:write`) y los asigna al rol `administrador` si no existen
- Levanta el servidor FastAPI en background con `AUTH_PROVIDER=local` y espera a que esté listo (polling `/api/health`)
- Autentica como `admin@camiula.com` y obtiene el JWT
- **Form Schemas CRUD:** PUT (create + update), GET list, GET by key, GET fallback, DELETE soft-delete, 422 por body inválido, 404 en clave inexistente
- **Soft-delete + auditoría:** verifica `status=T`, `deleted_at`, `deleted_by`, `created_by`, `updated_by` directamente en la tabla `form_schemas`
- **Specialties CRUD:** GET list, POST create, POST 409 duplicado, PUT update, PUT 404, PATCH toggle×2, PATCH 404, verifica `created_by`/`updated_by`
- **Appointment Stats:** GET sin filtros (verifica todos los campos del response), GET con `?fecha`, GET con `?doctor_id`, verifica prioridad de ruta vs `/{id}`
- **Medical Records:** GET sin registro, PUT create, GET tras upsert, PUT update, PATCH prepared, GET patient history con `limit` y `exclude`, verifica `schema_id` en historial
- Limpia el appointment y medical record de prueba al finalizar
- Salida con colores (PASS verde / FAIL rojo), resumen final, exit code 0 si todo pasa, 1 si algún test falla

**Uso:**
```bash
# Desde el worktree feature/nhm-endpoints:
./scripts/test_nhm_endpoints.sh
```

**Prerequisitos:**
- PostgreSQL corriendo con la DB `tesis_ula_local`
- Virtualenv en `../../.venv` relativo al worktree (i.e., el venv del repo principal)
- Puerto 8000 disponible

```bash
git add scripts/test_nhm_endpoints.sh
git commit -m "test(scripts): agregar script bash de integración para endpoints NHM"
```

---

## Resumen de orden

| # | Descripción corta | Tipo |
|---|---|---|
| 1 | Specialty entity + repo ABC | `feat(domain)` |
| 2 | MedicalRecord schema fields + history | `feat(domain)` |
| 3 | Appointment repo + get_stats | `feat(domain)` |
| 4 | UpsertMedicalRecordDTO + use case | `feat(appointments)` |
| 5 | Use cases: CRUD especialidades | `feat(appointments)` |
| 6 | Use cases: stats + historial | `feat(appointments)` |
| 7 | SQLAlchemy model: schema cols | `feat(appointments)` |
| 8 | SQLAlchemy repo: Specialty CRUD | `feat(appointments)` |
| 9 | SQLAlchemy repo: Appointment stats | `feat(appointments)` |
| 10 | SQLAlchemy repo: MedicalRecord history | `feat(appointments)` |
| 11 | Routes: specialty CRUD | `feat(appointments)` |
| 12 | Routes: appointment stats (orden correcto) | `feat(appointments)` |
| 13 | Routes: medical record historial | `feat(appointments)` |
| 14 | form_schemas: dominio | `feat(form-schemas)` |
| 15 | form_schemas: aplicación | `feat(form-schemas)` |
| 16 | form_schemas: infraestructura + auditoría completa | `feat(form-schemas)` |
| 17 | form_schemas: presentación + router | `feat(form-schemas)` |
| 18 | Alembic migration (con status + audit cols) | `chore(migrations)` |
| 19 | main.py wiring | `chore(app)` |
| 20 | Tests: specialty CRUD | `test(appointments)` |
| 21 | Tests: appointment stats | `test(appointments)` |
| 22 | Tests: patient history | `test(appointments)` |
| 23 | Tests: form_schemas | `test(form-schemas)` |
| 24 | Seeder: form_schemas | `feat(form-schemas)` |
| 25 | Docs | `docs` |
| 26 | Script bash integración NHM | `test(scripts)` |
