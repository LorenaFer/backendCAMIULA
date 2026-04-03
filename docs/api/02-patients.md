# Modulo: Gestion de Pacientes

CRUD de pacientes con busqueda por cedula/NHM y asignacion automatica de NHM.

---

## Interfaces TypeScript

```typescript
interface PatientCreate {
  cedula: string;
  first_name: string;
  last_name: string;
  university_relation: string;   // "estudiante" | "empleado" | "profesor" | "obrero"
  sex?: string | null;
  birth_date?: string | null;    // YYYY-MM-DD
  birth_place?: string | null;
  age?: number | null;
  marital_status?: string | null;
  religion?: string | null;
  origin?: string | null;
  home_address?: string | null;
  phone?: string | null;
  profession?: string | null;
  current_occupation?: string | null;
  work_address?: string | null;
  economic_classification?: string | null;
  family_relationship?: string | null;
  fk_holder_patient_id?: string | null;
  medical_data?: Record<string, any> | null;
  emergency_contact?: Record<string, any> | null;
}

interface PatientResponse {
  id: string;
  nhm: number;
  cedula: string;
  first_name: string;
  last_name: string;
  sex: string | null;
  birth_date: string | null;
  birth_place: string | null;
  age: number | null;
  marital_status: string | null;
  religion: string | null;
  origin: string | null;
  home_address: string | null;
  phone: string | null;
  profession: string | null;
  current_occupation: string | null;
  work_address: string | null;
  economic_classification: string | null;
  university_relation: string;
  family_relationship: string | null;
  fk_holder_patient_id: string | null;
  medical_data: Record<string, any>;
  emergency_contact: Record<string, any> | null;
  is_new: boolean;
  created_at: string | null;
}

interface PatientPublicResponse {
  id: string;
  nhm: number;
  first_name: string;
  last_name: string;
  university_relation: string;
  is_new: boolean;
}

interface MaxNhmResponse {
  max_nhm: number;
}
```

---

## Endpoints

### 1. `GET /patients`

Listar pacientes (paginado) o buscar por cedula/NHM.

**Auth:** JWT requerido

| Param | Tipo | Descripcion |
|-------|------|-------------|
| `nhm` | number | Busqueda exacta — retorna `PatientPublicResponse` |
| `cedula` | string | Busqueda exacta — retorna `PatientPublicResponse` |
| `page` | number | Pagina (default 1) |
| `page_size` | number | Tamano (default 20) |

Sin filtros: `PaginatedData<PatientResponse>`

---

### 2. `POST /patients`

Crear paciente. NHM se asigna automaticamente.

**Request Body:** `PatientCreate` | **Response (201):** `PatientResponse`

| Error | Condicion |
|-------|-----------|
| `409` | Cedula ya registrada |

---

### 3. `POST /patients/register`

Registro desde portal ULA (campos reducidos).

**Response (201):** `PatientPublicResponse`

---

### 4. `GET /patients/full`

Paciente completo por cedula o NHM.

**Query:** `cedula` o `nhm` | **Response:** `PatientResponse`

---

### 5. `GET /patients/max-nhm`

NHM mas alto registrado.

**Response:** `MaxNhmResponse`

---

### 6. `GET /patients/demographics`

Desglose demografico (para dashboard).

**Response:** `{ patients_by_type, patients_by_sex, first_time_count, returning_count }`
