# Modulo: Doctores, Especialidades y Disponibilidad

---

## Interfaces TypeScript

```typescript
interface DoctorResponse {
  id: string;
  fk_user_id: string;
  fk_specialty_id: string;
  first_name: string;
  last_name: string;
  doctor_status: string;
  specialty_name: string | null;
  created_at: string | null;
}

interface DoctorOptionResponse {
  id: string;
  first_name: string;
  last_name: string;
  fk_specialty_id: string;
  specialty_name: string | null;
  work_days: number[];
}

interface SpecialtyResponse {
  id: string;
  name: string;
  status: string | null;
  created_at: string | null;
}

interface AvailabilityResponse {
  id: string;
  fk_doctor_id: string;
  day_of_week: number;     // 0=Lun ... 6=Dom
  start_time: string;
  end_time: string;
  slot_duration: number;
  created_at: string | null;
}

interface ExceptionResponse {
  id: string;
  fk_doctor_id: string;
  exception_date: string;
  reason: string | null;
  created_at: string | null;
}
```

---

## Doctores

### 1. `GET /doctors` — Listar doctores activos

**Response:** `DoctorResponse[]`

### 2. `GET /doctors/options` — Lista ligera para selects

**Response:** `DoctorOptionResponse[]`

---

## Especialidades

### 3. `GET /specialties` — Listar especialidades

**Response:** `SpecialtyResponse[]`

### 4. `POST /specialties` — Crear

**Body:** `{ name: string }` | **Response (201):** `SpecialtyResponse`

### 5. `PUT /specialties/{id}` — Actualizar

**Body:** `{ name?: string }` | **Response:** `SpecialtyResponse`

### 6. `PATCH /specialties/{id}/toggle` — Activar/desactivar

**Response:** `SpecialtyResponse`

---

## Disponibilidad

### 7. `GET /doctors/{doctor_id}/availability` — Bloques horarios

**Query:** `dow?` (0-6) | **Response:** `AvailabilityResponse[]`

### 8. `POST /doctors/{doctor_id}/availability` — Crear bloque

**Body:** `{ day_of_week, start_time, end_time, slot_duration? }` (slot_duration default 30)

**Response (201):** `AvailabilityResponse`

### 9. `PATCH /doctors/{doctor_id}/availability/{block_id}` — Actualizar

**Response:** 204 No Content

### 10. `DELETE /doctors/{doctor_id}/availability/{block_id}` — Eliminar (soft)

**Response:** 204 No Content

### 11. `GET /doctors/{doctor_id}/exceptions` — Excepciones

**Query:** `date?` | **Response:** `ExceptionResponse[]`

### 12. `GET /doctors/availability/summary` — Resumen por especialidad

**Response:** `{ specialty, total_doctors, total_blocks }[]`
