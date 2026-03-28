# Guía de Commits — Feature NHM Endpoints

> **Fecha:** 2026-03-27
> **Branch origen:** `feature/nhm-endpoints`
> **Destino PR:** `main`
> **Propósito:** Orden y mensajes recomendados para commits granulares de esta feature.

Cada commit debe poder compilar y no romper tests ya existentes. Se recomienda seguir el orden listado.

---

## Convención de mensajes

```
<tipo>(<scope>): <descripción imperativa en español>
```

Tipos: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`
Scopes sugeridos: `domain`, `appointments`, `form-schemas`, `migrations`, `tests`, `docs`

---

## Commits recomendados

### Commit 1 — Dominio: entidad Specialty con soporte CRUD

**Mensaje:**
```
feat(domain): agregar campos CRUD a entidad Specialty
```

**Archivos:**
```
app/modules/appointments/domain/entities/specialty.py
app/modules/appointments/domain/repositories/specialty_repository.py
```

**Qué incluye:**
- Entidad `Specialty` con campo `is_active: bool = True`
- Repositorio abstracto `SpecialtyRepository` con métodos: `get_by_name`, `create`, `update`, `toggle`

---

### Commit 2 — Dominio: campos schema en MedicalRecord + historial

**Mensaje:**
```
feat(domain): agregar schema_id/schema_version a MedicalRecord y método get_patient_history
```

**Archivos:**
```
app/modules/appointments/domain/entities/medical_record.py
app/modules/appointments/domain/repositories/medical_record_repository.py
```

**Qué incluye:**
- Campos opcionales `schema_id` y `schema_version` en entidad `MedicalRecord`
- Método abstracto `get_patient_history(patient_id, limit, exclude_appointment_id)` en repositorio

---

### Commit 3 — Dominio: método get_stats en AppointmentRepository

**Mensaje:**
```
feat(domain): agregar método get_stats al repositorio de citas
```

**Archivos:**
```
app/modules/appointments/domain/repositories/appointment_repository.py
```

**Qué incluye:**
- Método abstracto `get_stats(fecha, doctor_id, specialty_id) -> Dict[str, Any]`

---

### Commit 4 — Application: DTO MedicalRecord actualizado

**Mensaje:**
```
feat(appointments): agregar schema_id y schema_version al DTO de historia médica
```

**Archivos:**
```
app/modules/appointments/application/dtos/medical_record_dto.py
```

**Qué incluye:**
- Campos opcionales `schema_id` y `schema_version` en `UpsertMedicalRecordDTO`

---

### Commit 5 — Application: casos de uso CRUD de especialidades

**Mensaje:**
```
feat(appointments): implementar casos de uso para CRUD de especialidades
```

**Archivos:**
```
app/modules/appointments/application/use_cases/create_specialty.py
app/modules/appointments/application/use_cases/update_specialty.py
app/modules/appointments/application/use_cases/toggle_specialty.py
```

**Qué incluye:**
- `CreateSpecialtyUseCase` — valida nombre único (409 si duplicado)
- `UpdateSpecialtyUseCase` — valida existencia y nombre no duplicado
- `ToggleSpecialtyUseCase` — valida existencia, delega toggle al repo

---

### Commit 6 — Application: casos de uso de stats y historial

**Mensaje:**
```
feat(appointments): implementar casos de uso para estadísticas y historial de paciente
```

**Archivos:**
```
app/modules/appointments/application/use_cases/get_appointment_stats.py
app/modules/appointments/application/use_cases/get_patient_medical_history.py
```

**Qué incluye:**
- `GetAppointmentStatsUseCase` — delega a `repo.get_stats()`
- `GetPatientMedicalHistoryUseCase` — delega a `repo.get_patient_history()`

---

### Commit 7 — Infrastructure: modelos SQLAlchemy actualizados

**Mensaje:**
```
feat(appointments): agregar columnas schema_id y schema_version al modelo MedicalRecord
```

**Archivos:**
```
app/modules/appointments/infrastructure/models.py
```

**Qué incluye:**
- `schema_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)`
- `schema_version: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)`

---

### Commit 8 — Infrastructure: repositorio Specialty actualizado

**Mensaje:**
```
feat(appointments): implementar métodos CRUD en SQLAlchemySpecialtyRepository
```

**Archivos:**
```
app/modules/appointments/infrastructure/repositories/sqlalchemy_specialty_repository.py
```

**Qué incluye:**
- Métodos `get_by_name`, `create`, `update`, `toggle`
- `_to_entity` mapea `is_active=model.status == RecordStatus.ACTIVE`

---

### Commit 9 — Infrastructure: repositorio Appointment con get_stats

**Mensaje:**
```
feat(appointments): implementar get_stats con agregaciones en SQLAlchemyAppointmentRepository
```

**Archivos:**
```
app/modules/appointments/infrastructure/repositories/sqlalchemy_appointment_repository.py
```

**Qué incluye:**
- `get_stats()` con consultas de agregación: by-status, by-specialty, by-doctor, first-time vs returning, by-patient-type, peak-hours
- Uso de `case()` de SQLAlchemy para conteos condicionales

---

### Commit 10 — Infrastructure: repositorio MedicalRecord actualizado

**Mensaje:**
```
feat(appointments): actualizar SQLAlchemyMedicalRecordRepository con schema_id y get_patient_history
```

**Archivos:**
```
app/modules/appointments/infrastructure/repositories/sqlalchemy_medical_record_repository.py
```

**Qué incluye:**
- `get_patient_history()` — consulta historial del paciente con límite y exclusión opcional
- `upsert()` y `_to_entity()` actualizados para `schema_id`/`schema_version`

---

### Commit 11 — Presentation: schemas y rutas CRUD de especialidades

**Mensaje:**
```
feat(appointments): agregar endpoints POST/PUT/PATCH para especialidades
```

**Archivos:**
```
app/modules/appointments/presentation/schemas/doctor_schema.py
app/modules/appointments/presentation/routes/doctor_routes.py
```

**Qué incluye:**
- Schemas `SpecialtyCreateRequest`, `SpecialtyUpdateRequest`
- Rutas: `POST /specialties`, `PUT /specialties/{id}`, `PATCH /specialties/{id}/toggle`
- Permiso requerido: `doctors:write`

---

### Commit 12 — Presentation: endpoint GET /appointments/stats

**Mensaje:**
```
feat(appointments): agregar endpoint de estadísticas GET /appointments/stats
```

**Archivos:**
```
app/modules/appointments/presentation/schemas/appointment_schema.py
app/modules/appointments/presentation/routes/appointment_routes.py
```

**Qué incluye:**
- Schema `AppointmentStatsResponse`
- Ruta `GET /appointments/stats` registrada ANTES de `GET /{appointment_id}` para evitar conflicto de path
- Filtros opcionales: `fecha`, `doctor_id`, `especialidad_id`

---

### Commit 13 — Presentation: rutas y schemas de historias médicas actualizados

**Mensaje:**
```
feat(appointments): agregar endpoint GET /medical-records/patient/{id} y campos de schema
```

**Archivos:**
```
app/modules/appointments/presentation/schemas/medical_record_schema.py
app/modules/appointments/presentation/routes/medical_record_routes.py
```

**Qué incluye:**
- `schema_id`/`schema_version` en `UpsertMedicalRecordRequest`, `MedicalRecordResponse`
- Clase `PatientHistoryEntry`
- Ruta `GET /medical-records/patient/{patient_id}` con parámetros `limit` y `exclude`

---

### Commit 14 — Módulo form_schemas: dominio

**Mensaje:**
```
feat(form-schemas): implementar entidad FormSchema con normalización de nombre
```

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
- `validate()` — verifica que `schema_json` contenga key `"sections"` como lista
- ABC `FormSchemaRepository` con métodos: `list_all`, `get_by_id`, `get_by_specialty_id_or_key`, `upsert`, `delete`

---

### Commit 15 — Módulo form_schemas: capa de aplicación

**Mensaje:**
```
feat(form-schemas): implementar DTOs y casos de uso para form schemas
```

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
- `GetFormSchemaUseCase` — con fallback a `"medicina-general"` si no existe schema para la especialidad
- `UpsertFormSchemaUseCase` — llama `schema.validate()`, lanza `AppException(422)` si falla
- `DeleteFormSchemaUseCase` — lanza 404 si no existe

---

### Commit 16 — Módulo form_schemas: infraestructura

**Mensaje:**
```
feat(form-schemas): implementar modelo SQLAlchemy y repositorio para form schemas
```

**Archivos:**
```
app/modules/form_schemas/infrastructure/__init__.py
app/modules/form_schemas/infrastructure/models.py
app/modules/form_schemas/infrastructure/repositories/__init__.py
app/modules/form_schemas/infrastructure/repositories/sqlalchemy_form_schema_repository.py
```

**Qué incluye:**
- `FormSchemaModel` — tabla `form_schemas` sin `SoftDeleteMixin`/`AuditMixin` (tabla de configuración)
- PK `id: String(100)` (semántico, no UUID)
- Columna `schema_json: JSONB`
- Upsert por PK semántico, hard delete

---

### Commit 17 — Módulo form_schemas: presentación

**Mensaje:**
```
feat(form-schemas): agregar rutas y schemas de presentación para form schemas
```

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
- `UpsertFormSchemaRequest` — valida presencia de `sections`
- 4 rutas: `GET /schemas`, `GET /schemas/{key}`, `PUT /schemas`, `DELETE /schemas/{id}`
- `_to_response()` — expande `schema_json` + agrega timestamps ISO; sin clase `FormSchemaResponse` (evita shadow de Pydantic)
- Permisos: `schemas:read` / `schemas:write`

---

### Commit 18 — Migración Alembic

**Mensaje:**
```
chore(migrations): agregar tabla form_schemas y campos schema_id/schema_version en medical_records
```

**Archivos:**
```
alembic/versions/a3f2e1b4c5d6_add_form_schemas_and_medical_record_schema_fields.py
alembic/env.py
```

**Qué incluye:**
- Creación tabla `form_schemas` (id, specialty_id, specialty_name, version, schema_json, created_at, updated_at)
- `ALTER TABLE medical_records ADD COLUMN schema_id VARCHAR(100)`
- `ALTER TABLE medical_records ADD COLUMN schema_version VARCHAR(20)`
- `downgrade()` revierte ambos cambios

---

### Commit 19 — Wiring: registrar módulo form_schemas en app principal

**Mensaje:**
```
chore(app): registrar router de form_schemas en main.py
```

**Archivos:**
```
app/main.py
```

**Qué incluye:**
- `from app.modules.form_schemas.router import router as form_schemas_router`
- `app.include_router(form_schemas_router, prefix="/api")`

---

### Commit 20 — Tests unitarios: CRUD de especialidades

**Mensaje:**
```
test(appointments): agregar tests unitarios para casos de uso de especialidades
```

**Archivos:**
```
tests/unit/appointments/test_specialty_crud.py
```

**Qué incluye:**
- Tests para `CreateSpecialtyUseCase` (éxito, duplicado 409)
- Tests para `UpdateSpecialtyUseCase` (éxito, no encontrado 404, nombre duplicado 409)
- Tests para `ToggleSpecialtyUseCase` (éxito, no encontrado 404)

---

### Commit 21 — Tests unitarios: estadísticas de citas

**Mensaje:**
```
test(appointments): agregar tests unitarios para GetAppointmentStatsUseCase
```

**Archivos:**
```
tests/unit/appointments/test_appointment_stats.py
```

**Qué incluye:**
- Test sin filtros (retorna estructura completa)
- Test con filtros de fecha y doctor

---

### Commit 22 — Tests unitarios: historial médico del paciente

**Mensaje:**
```
test(appointments): agregar tests unitarios para GetPatientMedicalHistoryUseCase
```

**Archivos:**
```
tests/unit/appointments/test_patient_history.py
```

**Qué incluye:**
- Test básico con límite y exclusión
- Test lista vacía

---

### Commit 23 — Tests unitarios: módulo form_schemas

**Mensaje:**
```
test(form-schemas): agregar tests unitarios para entidad FormSchema y casos de uso
```

**Archivos:**
```
tests/unit/form_schemas/__init__.py
tests/unit/form_schemas/test_entities.py
tests/unit/form_schemas/test_use_cases.py
```

**Qué incluye:**
- Tests de `FormSchema`: creación, `normalize_name()`, `validate()` (éxito y error 422)
- Tests de `ListFormSchemasUseCase`, `GetFormSchemaUseCase` (con y sin fallback), `UpsertFormSchemaUseCase`, `DeleteFormSchemaUseCase`

---

### Commit 24 — Documentación

**Mensaje:**
```
docs: agregar contrato de endpoints NHM implementados y guía de commits
```

**Archivos:**
```
docs/09-endpoints-nhm-implementados.md
docs/10-guia-commits-nhm.md
```

**Qué incluye:**
- Contrato final de endpoints con ejemplos de request/response
- Tabla de ajustes al contrato original
- Tabla de permisos
- Esta guía de commits granular

---

## Orden resumido

| # | Scope | Tipo |
|---|-------|------|
| 1 | `specialty` entity + repo ABC | `feat(domain)` |
| 2 | `medical_record` entity + repo ABC | `feat(domain)` |
| 3 | `appointment` repo ABC + get_stats | `feat(domain)` |
| 4 | `UpsertMedicalRecordDTO` | `feat(appointments)` |
| 5 | Use cases: CRUD especialidades | `feat(appointments)` |
| 6 | Use cases: stats + historial | `feat(appointments)` |
| 7 | SQLAlchemy model: schema cols | `feat(appointments)` |
| 8 | SQLAlchemy repo: Specialty | `feat(appointments)` |
| 9 | SQLAlchemy repo: Appointment stats | `feat(appointments)` |
| 10 | SQLAlchemy repo: MedicalRecord | `feat(appointments)` |
| 11 | Routes: specialty CRUD | `feat(appointments)` |
| 12 | Routes: appointment stats | `feat(appointments)` |
| 13 | Routes: medical record historial | `feat(appointments)` |
| 14 | form_schemas: dominio | `feat(form-schemas)` |
| 15 | form_schemas: aplicación | `feat(form-schemas)` |
| 16 | form_schemas: infraestructura | `feat(form-schemas)` |
| 17 | form_schemas: presentación | `feat(form-schemas)` |
| 18 | Alembic migration | `chore(migrations)` |
| 19 | main.py wiring | `chore(app)` |
| 20 | Tests: specialty CRUD | `test(appointments)` |
| 21 | Tests: appointment stats | `test(appointments)` |
| 22 | Tests: patient history | `test(appointments)` |
| 23 | Tests: form_schemas | `test(form-schemas)` |
| 24 | Docs | `docs` |

> **Tip:** los commits 1–19 son de implementación y deben ir en ese orden (dependencias de dominio → aplicación → infraestructura → presentación). Los commits de tests (20–23) pueden ir inmediatamente después de sus respectivos módulos si prefieres intercalarlos con la implementación.
