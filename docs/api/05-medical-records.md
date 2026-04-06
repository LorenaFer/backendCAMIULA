# Modulo: Historias Medicas y Schemas Dinamicos

---

## Interfaces TypeScript

```typescript
// ── Historias ──

interface MedicalRecordUpsert {
  fk_appointment_id: string;
  fk_patient_id: string;
  fk_doctor_id: string;
  evaluation?: any | null;       // JSON libre segun schema de la especialidad
  schema_id?: string | null;
  schema_version?: string | null;
}

interface MedicalRecordResponse {
  id: string;
  fk_appointment_id: string;
  fk_patient_id: string;
  fk_doctor_id: string;
  evaluation: any | null;
  is_prepared: boolean;
  prepared_at: string | null;
  prepared_by: string | null;
  schema_id: string | null;
  schema_version: string | null;
  status: string;
  created_at: string | null;
  updated_at: string | null;
}

interface PatientHistoryItem {
  id: string;
  date: string | null;
  specialty: string | null;
  doctor_name: string | null;
  diagnosis_description: string | null;
  diagnosis_code: string | null;
}

// ── Schemas de Formularios ──

interface FormSchemaUpsert {
  specialty_id: string;
  specialty_name: string;
  version: string;
  schema_json?: any | null;      // JSON Schema para renderizar formulario
}

interface FormSchemaResponse {
  id: string;
  specialty_id: string;
  specialty_name: string;
  version: string;
  schema_json: any | null;
  status: string;
  created_at: string | null;
  updated_at: string | null;
}
```

---

## Historias Medicas

### 1. `GET /medical-records?appointment_id={id}` — Buscar por cita

**Query:** `appointment_id` (requerido)

**Response:** `MedicalRecordResponse`

### 2. `GET /medical-records/{record_id}` — Buscar por ID

### 3. `PUT /medical-records` — Crear o actualizar (upsert)

**Body:** `MedicalRecordUpsert` | **Response:** `MedicalRecordResponse`

Si ya existe un registro para esa cita, lo actualiza. Si no, lo crea.

### 4. `PATCH /medical-records/{record_id}/prepared` — Marcar preparado

**Body:** `{ prepared_by: string }` | **Response:** `MedicalRecordResponse`

### 5. `GET /medical-records/patient/{patient_id}` — Historial del paciente

**Query:** `limit?` (default 5), `exclude?`

**Response:** `PatientHistoryItem[]`

### 6. `GET /medical-records/diagnostics/top` — Top diagnosticos

**Query:** `limit?` (default 5), `periodo?` (week | month | year)

---

## Schemas de Formularios

### 7. `GET /schemas` — Listar schemas

**Response:** `FormSchemaResponse[]`

### 8. `GET /schemas/{specialty_key}` — Schema por especialidad

Acepta UUID o nombre de especialidad.

### 9. `PUT /schemas` — Crear o actualizar schema

**Body:** `FormSchemaUpsert` | **Response:** `FormSchemaResponse`

### 10. `DELETE /schemas/{specialty_key}` — Eliminar (soft)
