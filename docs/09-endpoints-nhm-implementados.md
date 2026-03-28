# Endpoints NHM — Contratos Implementados

> **Fecha:** 2026-03-27
> **Branch:** `feature/nhm-endpoints`
> **Propósito:** Documento de confirmación para el equipo de frontend con los endpoints reales implementados, incluyendo ajustes respecto al contrato original.

---

## Convenciones (sin cambios respecto al contrato original)

| Convención | Valor |
|---|---|
| Base URL | `http://localhost:8000` |
| Prefijo | `/api` |
| Envelope | `{ "status": "success\|error", "message": "...", "data": T }` |
| IDs | UUID v4 strings |
| Fechas | ISO 8601 `"2026-03-26"` |
| Horas | `"09:00"` (24h) |
| Timestamps | ISO 8601 con timezone |

---

## Autenticación

Todos los endpoints requieren Bearer token JWT en el header `Authorization`.
El permiso requerido se indica por endpoint.

---

## 1. Pacientes (`/api/patients`)

> **Estado:** ✅ Ya implementados en la rama anterior.

| Método | Ruta | Permiso | Descripción |
|--------|------|---------|-------------|
| `GET` | `/api/patients?nhm={n}` | `patients:read` | Buscar por NHM |
| `GET` | `/api/patients?cedula={str}` | `patients:read` | Buscar por cédula |
| `GET` | `/api/patients/full?cedula={str}` | `patients:read` | Ficha completa |
| `GET` | `/api/patients/max-nhm` | `patients:read` | NHM máximo registrado |
| `POST` | `/api/patients` | `patients:create` | Registrar paciente |

---

## 2. Especialidades (`/api/specialties`)

> **Estado:** ✅ Nuevos en esta rama: POST, PUT, PATCH toggle.

| Método | Ruta | Permiso | Descripción |
|--------|------|---------|-------------|
| `GET` | `/api/specialties` | `doctors:read` | Listar especialidades activas |
| `POST` | `/api/specialties` | `doctors:write` | Crear especialidad |
| `PUT` | `/api/specialties/{id}` | `doctors:write` | Actualizar nombre |
| `PATCH` | `/api/specialties/{id}/toggle` | `doctors:write` | Activar/desactivar |

### GET /api/specialties
**Response:**
```json
{
  "status": "success",
  "message": "Listado de especialidades",
  "data": [
    { "id": "uuid", "nombre": "Medicina General", "activo": true }
  ]
}
```

### POST /api/specialties
**Body:**
```json
{ "nombre": "Cardiología" }
```
**Response (201):** `Especialidad` con `activo: true`

**Errores:**
- `409` si ya existe una especialidad con ese nombre.

### PUT /api/specialties/{id}
**Body:**
```json
{ "nombre": "Cardiología Intervencionista" }
```
**Response:** `Especialidad` actualizada

### PATCH /api/specialties/{id}/toggle
**Body:** ninguno
**Response:** `Especialidad` con `activo` invertido

---

## 3. Doctores (`/api/doctors`)

> **Estado:** ✅ Ya implementados en la rama anterior (sin cambios).

| Método | Ruta | Permiso | Descripción |
|--------|------|---------|-------------|
| `GET` | `/api/doctors?active=true` | `doctors:read` | Listar doctores |
| `GET` | `/api/doctors/options` | `doctors:read` | Dropdown doctores |
| `GET` | `/api/doctors/{id}/availability` | `doctors:read` | Bloques de disponibilidad |
| `GET` | `/api/doctors/{id}/availability?dow={1-5}` | `doctors:read` | Por día de semana |
| `GET` | `/api/doctors/{id}/exceptions?date={YYYY-MM-DD}` | `doctors:read` | Excepción por fecha |
| `POST` | `/api/doctors/{id}/availability` | `doctors:availability` | Crear bloque |
| `PATCH` | `/api/doctors/{id}/availability/{bloqueId}` | `doctors:availability` | Modificar bloque |
| `DELETE` | `/api/doctors/{id}/availability/{bloqueId}` | `doctors:availability` | Eliminar bloque |

---

## 4. Citas (`/api/appointments`)

> **Estado:** ✅ Ya implementados en la rama anterior. Nuevo en esta rama: `GET /stats`.

| Método | Ruta | Permiso | Descripción |
|--------|------|---------|-------------|
| `POST` | `/api/appointments` | `appointments:create` | Crear cita |
| `GET` | `/api/appointments` | `appointments:read` | Listar con filtros + paginación |
| `GET` | `/api/appointments/check-slot` | `appointments:read` | Verificar slot disponible |
| `GET` | `/api/appointments/stats` | `appointments:read` | **NUEVO** Estadísticas dashboard |
| `GET` | `/api/appointments/{id}` | `appointments:read` | Detalle con paciente y doctor |
| `PATCH` | `/api/appointments/{id}/status` | `appointments:update` | Cambiar estado |

### GET /api/appointments/stats
**Query params:** `fecha` (YYYY-MM-DD), `doctor_id` (UUID), `especialidad_id` (UUID)

**Response:**
```json
{
  "status": "success",
  "data": {
    "total": 45,
    "byStatus": {
      "pendiente": 10,
      "confirmada": 15,
      "atendida": 18,
      "cancelada": 2
    },
    "bySpecialty": [{ "name": "Medicina General", "count": 30 }],
    "byDoctor": [
      { "name": "Dr. Carlos Mendoza", "specialty": "Medicina General", "count": 25, "atendidas": 18 }
    ],
    "firstTimeCount": 8,
    "returningCount": 37,
    "byPatientType": { "empleado": 20, "estudiante": 15, "profesor": 5, "tercero": 5 },
    "dailyTrend": [],
    "peakHours": [{ "hour": "09:00", "count": 12 }]
  }
}
```

> **Nota:** `dailyTrend` retorna array vacío en esta versión. Requiere filtro de rango de fechas para ser significativo (siguiente iteración).

---

## 5. Historias Médicas (`/api/medical-records`)

> **Estado:** ✅ Ya implementados en la rama anterior. **Nuevos en esta rama:**
> - `GET /api/medical-records/patient/{id}` — historial previo
> - Campos `schema_id` y `schema_version` en PUT y GET

| Método | Ruta | Permiso | Descripción |
|--------|------|---------|-------------|
| `GET` | `/api/medical-records?appointment_id={id}` | `appointments:read` | Historia por cita |
| `PUT` | `/api/medical-records` | `appointments:update` | Upsert por cita_id |
| `GET` | `/api/medical-records/patient/{id}` | `appointments:read` | **NUEVO** Historial previo del paciente |
| `PATCH` | `/api/medical-records/{id}/prepared` | `appointments:update` | Marcar como preparada |

### PUT /api/medical-records
**Cambio respecto al contrato original:** se agregan `schema_id` y `schema_version` opcionales.

**Body:**
```json
{
  "cita_id": "uuid",
  "paciente_id": "uuid",
  "doctor_id": "uuid",
  "schema_id": "medicina-general-v1",
  "schema_version": "1.0",
  "evaluacion": { ... }
}
```

**Response:** `HistoriaMedica` (incluye `schema_id`, `schema_version`)

### GET /api/medical-records/patient/{pacienteId}
**Query params:**
- `limit` (int, default 5, max 50)
- `exclude` (UUID — excluir cita actual del historial)

**Response:**
```json
{
  "status": "success",
  "data": [
    {
      "id": "uuid",
      "cita_id": "uuid",
      "doctor_id": "uuid",
      "schema_id": "medicina-general-v1",
      "evaluacion": { ... },
      "preparado": true,
      "created_at": "2026-03-20T14:30:00Z"
    }
  ]
}
```

---

## 6. Schemas de Formularios (`/api/schemas`)

> **Estado:** ✅ **Nuevo módulo completo en esta rama.**

| Método | Ruta | Permiso | Descripción |
|--------|------|---------|-------------|
| `GET` | `/api/schemas` | `schemas:read` | Listar todos los schemas |
| `GET` | `/api/schemas/{specialtyKey}` | `schemas:read` | Schema por especialidad (con fallback) |
| `PUT` | `/api/schemas` | `schemas:write` | Upsert schema |
| `DELETE` | `/api/schemas/{schemaId}` | `schemas:write` | Eliminar schema |

### GET /api/schemas/{specialtyKey}

`specialtyKey` puede ser:
- El `specialty_id` normalizado: `"medicina-general"`
- El nombre con o sin acentos: `"Odontología"` → normalizado automáticamente a `"odontologia"`

**Fallback:** si no existe schema para la especialidad, retorna el de Medicina General. Si no existe el fallback, retorna `data: null`.

**Response:** estructura `MedicalFormSchema` del frontend:
```json
{
  "status": "success",
  "data": {
    "id": "medicina-general-v1",
    "version": "1.0",
    "specialtyId": "medicina-general",
    "specialtyName": "Medicina General",
    "sections": [...],
    "created_at": "2026-03-27T00:00:00Z",
    "updated_at": "2026-03-27T00:00:00Z"
  }
}
```

### PUT /api/schemas

**Body (estructura MedicalFormSchema del frontend):**
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

**Validación mínima:** el body debe contener el array `sections` (no vacía estructura).

**Nota:** El `specialtyId` es normalizado automáticamente por el backend
(ej: `"Medicina General"` → `"medicina-general"`).

**Response:** `MedicalFormSchema` con timestamps

**Errores:**
- `422` si `sections` está ausente del schema

---

## Ajustes al Contrato Original

| # | Endpoint | Ajuste | Razón |
|---|---|---|---|
| 1 | `POST/PUT/PATCH /api/specialties` | Permiso `doctors:write` (no `specialties:write`) | Alineado con permiso existente en el sistema |
| 2 | `PUT /api/medical-records` | Se agregan `schema_id` y `schema_version` opcionales | Necesario para vincular evaluaciones a su schema |
| 3 | `GET /api/appointments/stats` | `dailyTrend` retorna `[]` | Requiere rango de fechas — implementar en siguiente iteración |
| 4 | `GET /api/schemas/{specialtyKey}` | Normalización automática del nombre | El backend normaliza acentos/espacios al buscar |
| 5 | `DELETE /api/schemas/{schemaId}` | Recibe el `schema_id` exacto (ej: `"medicina-general-v1"`) | En vez del specialty key — permite eliminar versiones específicas |

---

## Tabla de Permisos Requeridos

| Permiso | Endpoints |
|---------|-----------|
| `patients:read` | `GET /patients`, `GET /patients/full`, `GET /patients/max-nhm` |
| `patients:create` | `POST /patients` |
| `doctors:read` | `GET /doctors`, `GET /specialties`, `GET /doctors/options`, `GET /doctors/{id}/availability`, `GET /doctors/{id}/exceptions` |
| `doctors:write` | `POST /specialties`, `PUT /specialties/{id}`, `PATCH /specialties/{id}/toggle` |
| `doctors:availability` | `POST/PATCH/DELETE /doctors/{id}/availability/{...}` |
| `appointments:read` | `GET /appointments`, `GET /appointments/check-slot`, `GET /appointments/stats`, `GET /appointments/{id}`, `GET /medical-records`, `GET /medical-records/patient/{id}` |
| `appointments:create` | `POST /appointments` |
| `appointments:update` | `PATCH /appointments/{id}/status`, `PUT /medical-records`, `PATCH /medical-records/{id}/prepared` |
| `schemas:read` | `GET /schemas`, `GET /schemas/{key}` |
| `schemas:write` | `PUT /schemas`, `DELETE /schemas/{id}` |

> **Nota:** Los permisos `schemas:read` y `schemas:write` son nuevos y deben ser agregados al seed de roles en la base de datos.
