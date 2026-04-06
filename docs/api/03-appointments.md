# Modulo: Citas Medicas

Agendamiento, slots de disponibilidad, estadisticas y heatmap.

---

## Interfaces TypeScript

```typescript
interface AppointmentCreate {
  fk_patient_id: string;
  fk_doctor_id: string;
  fk_specialty_id: string;
  appointment_date: string;      // YYYY-MM-DD
  start_time: string;            // HH:MM
  end_time: string;              // HH:MM
  duration_minutes: number;
  is_first_visit?: boolean;      // default false
  reason?: string | null;
  observations?: string | null;
}

interface AppointmentStatusUpdate {
  new_status: string;
  // "confirmed" | "in_progress" | "completed" | "cancelled" | "no_show"
}

interface AppointmentResponse {
  id: string;
  fk_patient_id: string;
  fk_doctor_id: string;
  fk_specialty_id: string;
  appointment_date: string | null;
  start_time: string;
  end_time: string;
  duration_minutes: number;
  is_first_visit: boolean;
  reason: string | null;
  observations: string | null;
  appointment_status: string;
  patient_name: string | null;
  patient_cedula: string | null;
  doctor_name: string | null;
  specialty_name: string | null;
  patient_university_relation: string | null;
  created_at: string | null;
}

interface SlotResponse {
  start_time: string;
  end_time: string;
  available: boolean;
}

interface CheckSlotResponse {
  occupied: boolean;
}
```

---

## Endpoints

### 1. `GET /appointments` — Listar citas (paginado, filtrable)

| Param | Tipo | Descripcion |
|-------|------|-------------|
| `fecha` | string | Filtrar por fecha YYYY-MM-DD |
| `doctor_id` | string | Filtrar por doctor |
| `especialidad_id` | string | Filtrar por especialidad |
| `estado` | string | Filtrar por estado |
| `q` | string | Busqueda por nombre/cedula |
| `mes` | string | Vista mensual (YYYY-MM) |
| `excluir_canceladas` | boolean | Default false |
| `page`, `page_size` | number | Paginacion |

**Response:** `PaginatedData<AppointmentResponse>`

### 2. `POST /appointments` — Crear cita

**Body:** `AppointmentCreate` | **Response (201):** `AppointmentResponse`

Error `409` si el slot esta ocupado.

### 3. `GET /appointments/{id}` — Detalle de cita

### 4. `PATCH /appointments/{id}/status` — Cambiar estado

**Body:** `AppointmentStatusUpdate`

### 5. `GET /appointments/available-slots` — Slots disponibles

**Query:** `doctor_id` (req), `fecha` (req), `es_nuevo?` | **Response:** `SlotResponse[]`

### 6. `GET /appointments/available-dates` — Fechas con disponibilidad

**Query:** `doctor_id` (req), `year` (req), `month` (req) | **Response:** `string[]`

### 7. `GET /appointments/check-slot` — Verificar slot

**Query:** `doctor_id` (req), `fecha` (req), `hora_inicio` (req) | **Response:** `CheckSlotResponse`

### 8. `GET /appointments/stats` — Estadisticas

**Query:** `fecha?`, `doctor_id?`, `especialidad_id?`, `estado?`

### 9. `GET /appointments/heatmap` — Heatmap dia x hora

**Query:** `fecha_desde` (req), `fecha_hasta` (req) | **Response:** `number[][]` (7x24)
