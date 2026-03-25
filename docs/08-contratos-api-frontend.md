# Contratos API — Guía de Integración Frontend

> Documento de referencia para el equipo de frontend. Mapea los endpoints del backend a lo que el frontend necesita.

**Base URL**: `http://localhost:8000/api`

**Autenticación**: JWT Bearer token en header `Authorization: Bearer {token}`

**Formato de respuestas**: Todas las respuestas siguen el envelope estándar:
```json
{
  "status": "success" | "error",
  "message": "Descripción",
  "data": T | null
}
```

---

## Diferencias Clave vs Contrato Original

| Aspecto | Contrato original | Backend real |
|---------|------------------|-------------|
| Base URL | `http://localhost:8000` | `http://localhost:8000/api` |
| IDs | `number` | `string` (UUID) |
| Rutas | Español (`/pacientes`) | Inglés (`/patients`) |
| Respuestas | JSON plano | Envelope `{ status, message, data }` |
| Paginación | `{ data, total, pageSize, hasNext }` | `{ items, pagination: { total, page, page_size, pages, has_next } }` |
| Campos | camelCase | snake_case |

---

## Tabla de Endpoints (25 totales)

| # | Método | Ruta Backend | Equivalente Frontend | Módulo |
|---|--------|-------------|---------------------|--------|
| 1 | POST | `/api/auth/login` | `/auth/login` | Auth |
| 2 | GET | `/api/users/me` | `/auth/me` | Auth |
| 3 | POST | `/api/auth/logout` | `/auth/logout` | Auth |
| 4 | GET | `/api/patients?nhm={nhm}` | `/pacientes?nhm={nhm}` | Patients |
| 5 | GET | `/api/patients?cedula={cedula}` | `/pacientes?cedula={cedula}` | Patients |
| 6 | GET | `/api/patients/full?cedula={cedula}` | `/pacientes/full?cedula={cedula}` | Patients |
| 7 | GET | `/api/patients/max-nhm` | `/pacientes/max-nhm` | Patients |
| 8 | POST | `/api/patients` | `/pacientes` | Patients |
| 9 | GET | `/api/doctors?active=true` | `/doctores?activo=true` | Appointments |
| 10 | GET | `/api/doctors/options` | `/doctores/opciones` | Appointments |
| 11 | GET | `/api/specialties` | `/especialidades` | Appointments |
| 12 | GET | `/api/doctors/{id}/availability` | `/doctores/{id}/disponibilidad` | Appointments |
| 13 | POST | `/api/doctors/{id}/availability` | `/doctores/{id}/disponibilidad` | Appointments |
| 14 | PATCH | `/api/doctors/{id}/availability/{blockId}` | `/doctores/{id}/disponibilidad/{bloqueId}` | Appointments |
| 15 | DELETE | `/api/doctors/{id}/availability/{blockId}` | `/doctores/{id}/disponibilidad/{bloqueId}` | Appointments |
| 16 | GET | `/api/doctors/{id}/exceptions?date={fecha}` | `/doctores/{id}/excepciones?fecha={fecha}` | Appointments |
| 17 | POST | `/api/appointments` | `/citas` | Appointments |
| 18 | GET | `/api/appointments?{filtros}` | `/citas?{filtros}` | Appointments |
| 19 | GET | `/api/appointments/{id}` | `/citas/{id}` | Appointments |
| 20 | PATCH | `/api/appointments/{id}/status` | `/citas/{id}/estado` | Appointments |
| 21 | GET | `/api/appointments/check-slot?{params}` | `/citas/check-slot?{params}` | Appointments |
| 22 | GET | `/api/medical-records?appointment_id={id}` | `/historias?cita_id={id}` | Appointments |
| 23 | PUT | `/api/medical-records` | `/historias` | Appointments |
| 24 | PATCH | `/api/medical-records/{id}/prepared` | `/historias/{id}/preparado` | Appointments |

---

## 1. Autenticación

### POST `/api/auth/login`

**Request:**
```json
{
  "identifier": "V-12345678",
  "password": "mipassword"
}
```
> `identifier` puede ser: email, cédula (V-12345678) o username.

**Response 200:**
```json
{
  "status": "success",
  "message": "Login exitoso",
  "data": {
    "user": {
      "id": "uuid-string",
      "name": "Carlos Mendoza",
      "role": "doctor",
      "initials": "CM",
      "doctor_id": "uuid-string-o-null"
    },
    "token": "eyJhbGciOiJI..."
  }
}
```

**Roles posibles**: `paciente`, `analista`, `doctor`, `admin`

### GET `/api/users/me`

**Headers:** `Authorization: Bearer {token}`

**Response 200:**
```json
{
  "status": "success",
  "message": "Perfil obtenido",
  "data": {
    "id": "uuid-string",
    "name": "Carlos Mendoza",
    "role": "doctor",
    "initials": "CM",
    "doctor_id": "uuid-string-o-null"
  }
}
```

### POST `/api/auth/logout`

**Response 200:**
```json
{
  "status": "success",
  "message": "Sesión cerrada",
  "data": { "ok": true }
}
```

---

## 2. Pacientes

### GET `/api/patients?nhm={nhm}` o `?cedula={cedula}`

**Response 200 (encontrado):**
```json
{
  "status": "success",
  "message": "Paciente encontrado",
  "data": {
    "id": "uuid",
    "nhm": 1001,
    "nombre": "Maria",
    "apellido": "Garcia",
    "relacion_univ": "empleado",
    "es_nuevo": false
  }
}
```

**Response 200 (no encontrado):**
```json
{
  "status": "success",
  "message": "Paciente no encontrado",
  "data": null
}
```

### GET `/api/patients/full?cedula={cedula}`

**Response 200:**
```json
{
  "status": "success",
  "message": "Ficha completa del paciente",
  "data": {
    "id": "uuid",
    "nhm": 1001,
    "cedula": "V-12345678",
    "nombre": "Maria",
    "apellido": "Garcia",
    "sexo": "F",
    "fecha_nacimiento": "1990-05-15",
    "lugar_nacimiento": "Merida",
    "edad": 35,
    "estado_civil": "casado",
    "religion": "catolico",
    "procedencia": "Merida",
    "direccion_habitacion": "Av. Los Proceres",
    "telefono": "0414-1234567",
    "profesion": "Ingeniera",
    "ocupacion_actual": "Docente",
    "direccion_trabajo": "ULA",
    "clasificacion_economica": "III",
    "relacion_univ": "empleado",
    "parentesco": null,
    "titular_nhm": null,
    "datos_medicos": {
      "tipo_sangre": "O+",
      "alergias": ["Penicilina"],
      "numero_contacto": "0414-1234567",
      "condiciones": []
    },
    "contacto_emergencia": {
      "nombre": "Juan Garcia",
      "parentesco": "esposo",
      "direccion": "Av. Los Proceres",
      "telefono": "0414-7654321"
    },
    "es_nuevo": false,
    "created_at": "2026-01-15T10:30:00Z"
  }
}
```

### GET `/api/patients/max-nhm`

**Response 200:**
```json
{
  "status": "success",
  "message": "Último NHM asignado",
  "data": { "max_nhm": 1042 }
}
```

### POST `/api/patients`

**Request:**
```json
{
  "cedula": "V-98765432",
  "nombre": "Pedro",
  "apellido": "Lopez",
  "relacion_univ": "profesor",
  "sexo": "M",
  "fecha_nacimiento": "1985-03-20",
  "telefono": "0412-9876543",
  "datos_medicos": {
    "tipo_sangre": "A+",
    "alergias": [],
    "numero_contacto": "0412-9876543"
  }
}
```

**Response 201:**
```json
{
  "status": "success",
  "message": "Paciente registrado exitosamente",
  "data": {
    "id": "uuid",
    "nhm": 1043,
    "cedula": "V-98765432",
    "nombre": "Pedro",
    "apellido": "Lopez",
    "relacion_univ": "profesor",
    "es_nuevo": true,
    "created_at": "2026-03-24T15:30:00Z"
  }
}
```

---

## 3. Doctores y Especialidades

### GET `/api/doctors?active=true`

**Response 200:**
```json
{
  "status": "success",
  "data": [
    {
      "id": "uuid",
      "nombre": "Carlos",
      "apellido": "Mendoza",
      "especialidad_id": "uuid",
      "activo": true,
      "especialidad": {
        "id": "uuid",
        "nombre": "Medicina General",
        "activo": true
      }
    }
  ]
}
```

### GET `/api/doctors/options`

**Response 200:**
```json
{
  "status": "success",
  "data": [
    {
      "id": "uuid",
      "nombre_completo": "Dr. Carlos Mendoza",
      "especialidad": "Medicina General",
      "especialidad_id": "uuid",
      "dias_trabajo": [1, 2, 3, 4, 5]
    }
  ]
}
```

### GET `/api/specialties`

**Response 200:**
```json
{
  "status": "success",
  "data": [
    { "id": "uuid", "nombre": "Medicina General", "activo": true },
    { "id": "uuid", "nombre": "Pediatría", "activo": true }
  ]
}
```

---

## 4. Disponibilidad

### GET `/api/doctors/{id}/availability?dow={1-5}`

**Response 200:**
```json
{
  "status": "success",
  "data": [
    {
      "id": "uuid",
      "doctor_id": "uuid",
      "day_of_week": 1,
      "hora_inicio": "08:00",
      "hora_fin": "12:00",
      "duracion_slot": 30
    }
  ]
}
```

### POST `/api/doctors/{id}/availability`

**Request:**
```json
{
  "doctor_id": "uuid",
  "day_of_week": 2,
  "hora_inicio": "08:00",
  "hora_fin": "12:00",
  "duracion_slot": 30
}
```

### GET `/api/doctors/{id}/exceptions?date=2026-04-15`

**Response 200:**
```json
{
  "status": "success",
  "data": { "excepcion": true }
}
```

---

## 5. Citas

### POST `/api/appointments`

**Request:**
```json
{
  "paciente_id": "uuid",
  "doctor_id": "uuid",
  "especialidad_id": "uuid",
  "fecha": "2026-04-15",
  "hora_inicio": "09:00",
  "hora_fin": "09:30",
  "duracion_min": 30,
  "es_primera_vez": false,
  "motivo_consulta": "Control",
  "observaciones": "Renovación de recipe"
}
```

**Response 201:**
```json
{
  "status": "success",
  "message": "Cita creada exitosamente",
  "data": {
    "id": "uuid",
    "paciente_id": "uuid",
    "doctor_id": "uuid",
    "especialidad_id": "uuid",
    "fecha": "2026-04-15",
    "hora_inicio": "09:00",
    "hora_fin": "09:30",
    "duracion_min": 30,
    "es_primera_vez": false,
    "estado": "pendiente",
    "motivo_consulta": "Control",
    "created_at": "2026-03-24T15:30:00Z"
  }
}
```

### GET `/api/appointments?{filtros}`

**Query params:** `fecha`, `doctor_id`, `especialidad_id`, `estado`, `q`, `mes` (YYYY-MM), `excluir_canceladas`, `page`, `page_size`

**Response 200:**
```json
{
  "status": "success",
  "data": {
    "items": [
      {
        "id": "uuid",
        "fecha": "2026-04-15",
        "hora_inicio": "09:00",
        "hora_fin": "09:30",
        "estado": "pendiente",
        "paciente": {
          "id": "uuid",
          "nhm": 1001,
          "nombre": "Maria",
          "apellido": "Garcia",
          "cedula": "V-12345678",
          "relacion_univ": "empleado"
        },
        "doctor": {
          "id": "uuid",
          "nombre": "Carlos",
          "apellido": "Mendoza",
          "especialidad": "Medicina General"
        }
      }
    ],
    "pagination": {
      "total": 150,
      "page": 1,
      "page_size": 25,
      "pages": 6,
      "has_next": true
    }
  }
}
```

### GET `/api/appointments/check-slot?doctor_id={}&fecha={}&hora_inicio={}`

**Response 200:**
```json
{
  "status": "success",
  "data": { "ocupado": false }
}
```

### PATCH `/api/appointments/{id}/status`

**Request:**
```json
{ "estado": "confirmada" }
```

**Valores válidos:** `pendiente`, `confirmada`, `atendida`, `cancelada`, `no_asistio`

---

## 6. Historias Médicas

### GET `/api/medical-records?appointment_id={id}`

**Response 200 (encontrada):**
```json
{
  "status": "success",
  "data": {
    "id": "uuid",
    "cita_id": "uuid",
    "paciente_id": "uuid",
    "doctor_id": "uuid",
    "evaluacion": {
      "motivo_consulta": "Dolor de cabeza",
      "anamnesis": "...",
      "examen_fisico": { "ta": "120/80", "fc": "72" },
      "diagnostico": { "cie10": "R51", "descripcion": "Cefalea tensional" },
      "tratamiento": "Ibuprofeno 400mg",
      "indicaciones": "Reposo"
    },
    "preparado": false,
    "preparado_at": null,
    "created_at": "2026-03-24T15:30:00Z"
  }
}
```

### PUT `/api/medical-records`

**Request:**
```json
{
  "cita_id": "uuid",
  "paciente_id": "uuid",
  "doctor_id": "uuid",
  "evaluacion": { "motivo_consulta": "...", "diagnostico": { ... } }
}
```

### PATCH `/api/medical-records/{id}/prepared`

**Request:**
```json
{ "preparado_por": "doctor:doc-1" }
```

---

## Códigos de Error

| Código | Significado | Ejemplo |
|--------|------------|---------|
| 401 | No autenticado / token inválido | `{ "status": "error", "message": "Token inválido o expirado" }` |
| 403 | Sin permisos | `{ "status": "error", "message": "Permiso requerido: patients:create" }` |
| 404 | No encontrado | `{ "status": "error", "message": "Paciente no encontrado" }` |
| 409 | Conflicto | `{ "status": "error", "message": "Ya existe un paciente con esta cédula" }` |
| 422 | Validación | `{ "status": "error", "message": "Error de validación", "data": [...] }` |

---

## Reglas de Negocio Validadas por el Backend

| Regla | Detalle |
|-------|---------|
| Mínimo 2 días para agendar | `fecha >= hoy + 2 días` |
| Sin doble reserva | Un doctor no puede tener 2 citas en el mismo slot |
| Cédula única | No se puede registrar 2 pacientes con la misma cédula |
| NHM auto-incremental | Generado por el backend (secuencia PostgreSQL) |
| Familiar requiere titular | Si `relacion_univ = "tercero"` → `parentesco` y `titular_nhm` obligatorios |
| Primera vez = 60 min | Si `es_primera_vez = true` → `duracion_min = 60` |
| Transiciones de estado | `pendiente → confirmada/cancelada`, `confirmada → atendida/cancelada/no_asistio` |
