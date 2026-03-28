# NHM Endpoints — Documentación Completa

> **Branch:** `feature/nhm-endpoints`
> **Base URL:** `http://localhost:8000`
> **Prefijo API:** `/api`

---

## Convenciones

| Convención | Valor |
|---|---|
| Envelope éxito | `{ "status": "success", "message": "...", "data": T }` |
| Envelope error | `{ "status": "error", "message": "...", "data": null }` |
| IDs | UUID v4 strings |
| Fechas | ISO 8601 `"2026-03-26"` |
| Horas | `"09:00"` (24h, HH:MM) |
| Timestamps | ISO 8601 con timezone |
| Auth | Header `Authorization: Bearer <JWT>` |

---

## Módulos implementados en esta branch

1. [Especialidades — CRUD](#1-especialidades)
2. [Appointments — Stats](#2-appointments-stats)
3. [Medical Records — Historial paciente + campos schema](#3-medical-records)
4. [Form Schemas — Módulo nuevo completo](#4-form-schemas)

---

## 1. Especialidades

**Prefijo:** `/api/specialties`

Los endpoints GET ya existían. Los de escritura (POST/PUT/PATCH) son nuevos en esta branch.

### GET /api/specialties

Listar todas las especialidades (activas e inactivas).

**Auth:** `doctors:read`

**Response 200:**
```json
{
  "status": "success",
  "message": "Listado de especialidades",
  "data": [
    { "id": "uuid", "nombre": "Medicina General", "activo": true },
    { "id": "uuid", "nombre": "Odontología", "activo": false }
  ]
}
```

---

### POST /api/specialties

Crear nueva especialidad.

**Auth:** `doctors:write`

**Request body:**
```json
{ "nombre": "Cardiología" }
```

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `nombre` | string | ✅ | Nombre de la especialidad |

**Response 201:**
```json
{
  "status": "success",
  "message": "Especialidad creada",
  "data": { "id": "uuid", "nombre": "Cardiología", "activo": true }
}
```

**Errores:**
| Código | Descripción |
|--------|-------------|
| `409` | Ya existe una especialidad con ese nombre |
| `422` | Body inválido |

---

### PUT /api/specialties/{specialty_id}

Actualizar nombre de una especialidad.

**Auth:** `doctors:write`

**Path params:** `specialty_id` (UUID)

**Request body:**
```json
{ "nombre": "Cardiología Intervencionista" }
```

**Response 200:**
```json
{
  "status": "success",
  "message": "Especialidad actualizada",
  "data": { "id": "uuid", "nombre": "Cardiología Intervencionista", "activo": true }
}
```

**Errores:**
| Código | Descripción |
|--------|-------------|
| `404` | Especialidad no encontrada |
| `409` | Ya existe otra especialidad con ese nombre |

---

### PATCH /api/specialties/{specialty_id}/toggle

Alternar estado activo/inactivo.

**Auth:** `doctors:write`

**Path params:** `specialty_id` (UUID)

**Body:** ninguno

**Response 200:**
```json
{
  "status": "success",
  "message": "Estado de especialidad actualizado",
  "data": { "id": "uuid", "nombre": "Cardiología", "activo": false }
}
```

**Errores:**
| Código | Descripción |
|--------|-------------|
| `404` | Especialidad no encontrada |

---

## 2. Appointments — Stats

**Endpoint nuevo.** Los demás endpoints de `/api/appointments` ya existían.

### GET /api/appointments/stats

Estadísticas de citas para el dashboard. Registrado **antes** de `GET /{id}` para evitar conflicto de path.

**Auth:** `appointments:read`

**Query params (todos opcionales):**

| Param | Tipo | Descripción |
|-------|------|-------------|
| `fecha` | date `YYYY-MM-DD` | Filtrar por fecha exacta |
| `doctor_id` | UUID string | Filtrar por doctor |
| `especialidad_id` | UUID string | Filtrar por especialidad |

**Response 200:**
```json
{
  "status": "success",
  "message": "Estadísticas de citas",
  "data": {
    "total": 45,
    "byStatus": {
      "pendiente": 10,
      "confirmada": 15,
      "atendida": 18,
      "cancelada": 2
    },
    "bySpecialty": [
      { "name": "Medicina General", "count": 30 }
    ],
    "byDoctor": [
      { "name": "Dr. Carlos Mendoza", "specialty": "Medicina General", "count": 25, "atendidas": 18 }
    ],
    "firstTimeCount": 8,
    "returningCount": 37,
    "byPatientType": {
      "empleado": 20,
      "estudiante": 15,
      "profesor": 5,
      "tercero": 5
    },
    "dailyTrend": [],
    "peakHours": [
      { "hour": "09:00", "count": 12 }
    ]
  }
}
```

> **Nota:** `dailyTrend` retorna array vacío en esta versión. Requiere filtro de rango de fechas (próxima iteración).

---

## 3. Medical Records

**Prefijo:** `/api/medical-records`

Dos cambios respecto a la rama anterior:
1. Campos `schema_id` y `schema_version` opcionales en PUT y GET.
2. Nuevo endpoint `GET /patient/{patient_id}`.

### GET /api/medical-records?appointment_id={id}

*(Sin cambios respecto a la rama anterior, excepto que ahora devuelve `schema_id` y `schema_version`.)*

**Auth:** `appointments:read`

**Query params:**

| Param | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `appointment_id` | UUID | ✅ | ID de la cita |

**Response 200:**
```json
{
  "status": "success",
  "message": "Historia médica encontrada",
  "data": {
    "id": "uuid",
    "cita_id": "uuid",
    "paciente_id": "uuid",
    "doctor_id": "uuid",
    "schema_id": "medicina-general-v1",
    "schema_version": "1.0",
    "evaluacion": { "motivo_consulta": "Control", "presion": "120/80" },
    "preparado": false,
    "preparado_at": null,
    "created_at": "2026-03-27T10:00:00Z",
    "updated_at": "2026-03-27T10:00:00Z"
  }
}
```

Si no existe historia médica: `data: null`.

---

### PUT /api/medical-records

Crear o actualizar historia médica (upsert por `cita_id`).

**Auth:** `appointments:update`

**Request body:**
```json
{
  "cita_id": "uuid",
  "paciente_id": "uuid",
  "doctor_id": "uuid",
  "schema_id": "medicina-general-v1",
  "schema_version": "1.0",
  "evaluacion": {
    "motivo_consulta": "Control rutinario",
    "presion_arterial": "120/80",
    "temperatura": 36.5
  }
}
```

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `cita_id` | UUID | ✅ | ID de la cita (PK del upsert) |
| `paciente_id` | UUID | ✅ | ID del paciente |
| `doctor_id` | UUID | ✅ | ID del doctor |
| `schema_id` | string | ❌ | ID del schema usado (`"medicina-general-v1"`) |
| `schema_version` | string | ❌ | Versión del schema (`"1.0"`) |
| `evaluacion` | object | ✅ | JSON libre con los campos del formulario |

**Response 200:** Historia médica guardada (mismo shape que GET).

---

### GET /api/medical-records/patient/{patient_id}

**NUEVO.** Historial médico previo del paciente. Diseñado para pre-cargar el contexto clínico al abrir la consulta actual.

**Auth:** `appointments:read`

**Path params:** `patient_id` (UUID)

**Query params:**

| Param | Tipo | Default | Descripción |
|-------|------|---------|-------------|
| `limit` | int (1–50) | `5` | Máximo de registros a retornar |
| `exclude` | UUID | — | Excluir esta cita del historial (tipicamente la cita actual) |

**Response 200:**
```json
{
  "status": "success",
  "message": "Historial médico del paciente",
  "data": [
    {
      "id": "uuid",
      "cita_id": "uuid",
      "doctor_id": "uuid",
      "schema_id": "medicina-general-v1",
      "evaluacion": { "motivo_consulta": "Dolor de cabeza" },
      "preparado": true,
      "created_at": "2026-03-20T14:30:00Z"
    }
  ]
}
```

---

### PATCH /api/medical-records/{record_id}/prepared

Marcar historia médica como preparada.

**Auth:** `appointments:update`

**Path params:** `record_id` (UUID)

**Request body:**
```json
{ "preparado_por": "uuid-del-usuario" }
```

**Response 200:**
```json
{
  "status": "success",
  "message": "Historia marcada como preparada",
  "data": null
}
```

---

## 4. Form Schemas

**Prefijo:** `/api/schemas`

**Módulo nuevo completo.** Almacena y sirve la estructura de los formularios médicos dinámicos por especialidad. El backend solo persiste el JSON; el renderizado ocurre en el frontend.

**Auditoría completa:** la tabla `form_schemas` cumple el estándar de trazabilidad del proyecto (`SoftDeleteMixin` + `AuditMixin`):

| Campo | Descripción |
|-------|-------------|
| `status` | `A` (active) / `I` (inactive) / `T` (trash/eliminado) |
| `created_by` | UUID del usuario que creó el schema |
| `updated_by` | UUID del usuario que realizó la última actualización |
| `deleted_at` | Timestamp del soft-delete |
| `deleted_by` | UUID del usuario que realizó el soft-delete |

> `DELETE /schemas/{id}` realiza **soft-delete** (status → T). Los schemas eliminados no aparecen en `GET /schemas` ni en `GET /schemas/{key}`.

### GET /api/schemas

Listar todos los schemas de formularios disponibles.

**Auth:** `schemas:read`

**Response 200:**
```json
{
  "status": "success",
  "message": "Listado de schemas",
  "data": [
    {
      "id": "medicina-general-v1",
      "version": "1.0",
      "specialtyId": "medicina-general",
      "specialtyName": "Medicina General",
      "sections": [...],
      "created_at": "2026-03-27T00:00:00Z",
      "updated_at": "2026-03-27T00:00:00Z"
    }
  ]
}
```

---

### GET /api/schemas/{specialty_key}

Obtener schema de una especialidad. Incluye fallback automático.

**Auth:** `schemas:read`

**Path params:** `specialty_key` — puede ser:
- El `specialty_id` normalizado: `"medicina-general"`
- El `schema_id` exacto: `"medicina-general-v1"`
- Un nombre libre (el backend lo normaliza): `"Odontología"` → `"odontologia"`

**Comportamiento fallback:**
1. Busca schema para `specialty_key` (exact match en `specialty_id` o `id`).
2. Si no existe, retorna el schema de `"medicina-general"`.
3. Si tampoco existe, retorna `data: null`.

**Response 200:**
```json
{
  "status": "success",
  "message": "Schema encontrado",
  "data": {
    "id": "medicina-general-v1",
    "version": "1.0",
    "specialtyId": "medicina-general",
    "specialtyName": "Medicina General",
    "sections": [
      {
        "id": "motivo",
        "title": "Motivo de Consulta",
        "groups": [
          {
            "id": "motivo-group",
            "fields": [
              {
                "key": "motivo_consulta",
                "type": "textarea",
                "label": "Motivo de consulta",
                "validation": { "required": true }
              }
            ]
          }
        ]
      }
    ],
    "created_at": "2026-03-27T00:00:00Z",
    "updated_at": "2026-03-27T00:00:00Z"
  }
}
```

---

### PUT /api/schemas

Crear o actualizar schema de formulario (upsert por `id`).

**Auth:** `schemas:write`

**Request body** — estructura `MedicalFormSchema` del frontend:

```json
{
  "id": "medicina-general-v1",
  "version": "1.0",
  "specialtyId": "medicina-general",
  "specialtyName": "Medicina General",
  "sections": [
    {
      "id": "motivo",
      "title": "Motivo de Consulta",
      "groups": [
        {
          "id": "motivo-group",
          "fields": [
            {
              "key": "motivo_consulta",
              "type": "textarea",
              "label": "Motivo de consulta",
              "validation": { "required": true }
            }
          ]
        }
      ]
    }
  ]
}
```

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `id` | string | ✅ | ID semántico del schema (`"medicina-general-v1"`) |
| `version` | string | ✅ | Versión (`"1.0"`) |
| `specialtyId` | string | ✅ | Normalizado automáticamente por el backend |
| `specialtyName` | string | ✅ | Nombre legible de la especialidad |
| `sections` | array | ✅ | Secciones del formulario |

**Response 200:** Schema guardado con timestamps.

**Errores:**
| Código | Descripción |
|--------|-------------|
| `422` | `sections` ausente o no es array |

---

### DELETE /api/schemas/{schema_key}

**Soft-delete** de un schema. Cambia `status → T` y registra `deleted_at` / `deleted_by`. No elimina el registro físicamente.

**Auth:** `schemas:write`

**Path params:** `schema_key` — el `id` semántico exacto del schema (ej: `"medicina-general-v1"`).

**Response 200:**
```json
{
  "status": "success",
  "message": "Schema eliminado",
  "data": null
}
```

**Errores:**
| Código | Descripción |
|--------|-------------|
| `404` | Schema no encontrado (o ya fue eliminado) |

---

## Tabla de Permisos

| Permiso | Endpoints |
|---------|-----------|
| `doctors:read` | `GET /specialties`, `GET /doctors`, `GET /doctors/options`, `GET /doctors/{id}/availability`, `GET /doctors/{id}/exceptions` |
| `doctors:write` | `POST /specialties`, `PUT /specialties/{id}`, `PATCH /specialties/{id}/toggle` |
| `doctors:availability` | `POST/PATCH/DELETE /doctors/{id}/availability/...` |
| `appointments:read` | `GET /appointments`, `GET /appointments/check-slot`, `GET /appointments/stats`, `GET /appointments/{id}`, `GET /medical-records`, `GET /medical-records/patient/{id}` |
| `appointments:create` | `POST /appointments` |
| `appointments:update` | `PATCH /appointments/{id}/status`, `PUT /medical-records`, `PATCH /medical-records/{id}/prepared` |
| `schemas:read` | `GET /schemas`, `GET /schemas/{key}` |
| `schemas:write` | `PUT /schemas`, `DELETE /schemas/{id}` |

> **Nota:** `schemas:read` y `schemas:write` son permisos nuevos. Deben agregarse al seed de roles en la base de datos antes del despliegue.

---

## Cambios respecto al contrato original (08-contratos-api-frontend.md)

| # | Endpoint | Cambio | Razón |
|---|---|---|---|
| 1 | `POST/PUT/PATCH /specialties` | Permiso `doctors:write` en lugar de `specialties:write` | Alineado con el sistema de permisos existente |
| 2 | `PUT /medical-records` | Se agregan `schema_id` y `schema_version` opcionales | Vincular evaluaciones a su schema de formulario |
| 3 | `GET /appointments/stats` | `dailyTrend` retorna `[]` | Requiere rango de fechas — próxima iteración |
| 4 | `GET /schemas/{specialtyKey}` | Normalización automática de nombre con fallback | El backend normaliza acentos/espacios al buscar |
| 5 | `DELETE /schemas/{schemaId}` | Soft-delete (`status=T`) en lugar de hard delete | Cumple estándar de auditoría del proyecto |
| 6 | `PUT /schemas` | `created_by` / `updated_by` se llenan con el user del token | Cumple estándar de trazabilidad del proyecto |

## Datos Iniciales (Seeders)

La tabla `form_schemas` incluye un seeder con schemas base para las especialidades más usadas en CAMIULA:

| Schema ID | Especialidad | Secciones |
|-----------|-------------|-----------|
| `medicina-general-v1` | Medicina General | Motivo, Signos Vitales, Evaluación Clínica |
| `odontologia-v1` | Odontología | Motivo, Evaluación Dental |
| `psicologia-v1` | Psicología | Motivo, Evaluación Psicológica |
| `nutricion-v1` | Nutrición | Motivo, Datos Antropométricos, Hábitos |

```bash
# Sembrar solo form_schemas
python -m app.shared.database.seeder form_schemas

# Sembrar todos los módulos
python -m app.shared.database.seeder
```
