# Modulo: Inventario — Medicamentos, Proveedores y Lotes

Todos los endpoints llevan prefijo `/inventory/`.

---

## Interfaces TypeScript

```typescript
// ── Medicamentos ──

interface MedicationCreate {
  code: string;
  generic_name: string;
  pharmaceutical_form: string;
  unit_measure: string;
  controlled_substance: boolean;
  requires_refrigeration: boolean;
  commercial_name?: string | null;
  concentration?: string | null;
  therapeutic_class?: string | null;
}

interface MedicationResponse {
  id: string;
  code: string;
  generic_name: string;
  commercial_name: string | null;
  pharmaceutical_form: string;
  concentration: string | null;
  unit_measure: string;
  therapeutic_class: string | null;
  controlled_substance: boolean;
  requires_refrigeration: boolean;
  medication_status: string;     // "active" | "inactive"
  current_stock: number;
  created_at: string | null;
}

interface MedicationOptionResponse {
  id: string;
  code: string;
  generic_name: string;
  pharmaceutical_form: string;
  unit_measure: string;
  current_stock: number;
}

// ── Proveedores ──

interface SupplierCreate {
  name: string;
  rif: string;
  phone?: string | null;
  email?: string | null;
  contact_name?: string | null;
  payment_terms?: string | null;
}

interface SupplierResponse {
  id: string;
  name: string;
  rif: string;
  phone: string | null;
  email: string | null;
  contact_name: string | null;
  payment_terms: string | null;
  supplier_status: string;       // "active" | "inactive"
  created_at: string | null;
}

// ── Lotes ──

interface BatchResponse {
  id: string;
  fk_medication_id: string;
  fk_supplier_id: string | null;
  lot_number: string;
  expiration_date: string;
  quantity_received: number;
  quantity_available: number;
  unit_cost: number | null;
  batch_status: string;          // "available" | "depleted" | "expired" | "quarantine"
  received_at: string;
}
```

---

## Medicamentos

### 1. `GET /inventory/medications` — Listar (paginado)

| Param | Descripcion |
|-------|-------------|
| `search` | Buscar por nombre generico/comercial |
| `status` | Filtrar por estado |
| `therapeutic_class` | Filtrar por clase terapeutica |
| `page`, `page_size` | Paginacion |

**Response:** `PaginatedData<MedicationResponse>`

### 2. `GET /inventory/medications/options` — Lista ligera para selects

**Query:** `search?`, `limit?` (default 100) | **Response:** `MedicationOptionResponse[]`

### 3. `GET /inventory/medications/{id}` — Detalle

### 4. `POST /inventory/medications` — Crear

**Body:** `MedicationCreate` | **Response (201):** `MedicationResponse`

### 5. `PUT /inventory/medications/{id}` — Actualizar

### 6. `DELETE /inventory/medications/{id}` — Eliminar (soft)

---

## Proveedores

### 7. `GET /inventory/suppliers` — Listar (paginado)

**Query:** `search?`, `status?`, `page`, `page_size`

### 8. `GET /inventory/suppliers/options` — Lista para selects

**Response:** `{ id, name, rif }[]`

### 9. `GET /inventory/suppliers/{id}` — Detalle

### 10. `POST /inventory/suppliers` — Crear

Error `409` si RIF duplicado.

### 11. `PATCH /inventory/suppliers/{id}` — Actualizar

---

## Lotes

### 12. `GET /inventory/batches` — Listar (paginado)

| Param | Descripcion |
|-------|-------------|
| `medication_id` | Filtrar por medicamento |
| `status` | Filtrar por estado del lote |
| `expiring_before` | Fecha limite de vencimiento (YYYY-MM-DD) |

### 13. `GET /inventory/batches/{id}` — Detalle
