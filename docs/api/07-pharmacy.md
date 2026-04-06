# Modulo: Farmacia — Recetas, Despachos, Limites y Reportes

Todos los endpoints llevan prefijo `/inventory/`.

---

## Interfaces TypeScript

```typescript
// ── Recetas ──

interface PrescriptionCreate {
  fk_appointment_id: string;
  fk_patient_id: string;
  fk_doctor_id: string;
  notes?: string | null;
  items: {
    medication_id: string;
    quantity_prescribed: number;
    dosage_instructions?: string | null;
    duration_days?: number | null;
  }[];
}

interface PrescriptionResponse {
  id: string;
  prescription_number: string;
  fk_appointment_id: string;
  fk_patient_id: string;
  fk_doctor_id: string;
  prescription_date: string;
  notes: string | null;
  prescription_status: string;   // "pending" | "dispensed" | "cancelled"
  items: {
    id: string;
    fk_medication_id: string;
    quantity_prescribed: number;
    dosage_instructions: string | null;
    duration_days: number | null;
  }[];
  created_at: string | null;
}

// ── Despachos ──

interface DispatchCreate {
  fk_prescription_id: string;
  patient_type?: string;         // default "all"
  notes?: string | null;
}

interface DispatchResponse {
  id: string;
  fk_prescription_id: string;
  fk_patient_id: string;
  fk_pharmacist_id: string;
  dispatch_date: string;
  notes: string | null;
  dispatch_status: string;       // "completed" | "cancelled"
  items: {
    id: string;
    fk_batch_id: string;
    fk_medication_id: string;
    quantity_dispatched: number;
  }[];
  created_at: string | null;
}

interface DispatchValidationResponse {
  can_dispatch: boolean;
  prescription_id: string;
  patient_id: string;
  items: {
    medication_id: string;
    generic_name: string;
    quantity_prescribed: number;
    quantity_available: number;
    monthly_limit: number | null;
    monthly_used: number;
    monthly_remaining: number | null;
    has_exception: boolean;
    can_dispatch: boolean;
    block_reason: string | null;
  }[];
}

// ── Limites ──

interface DispatchLimitResponse {
  id: string;
  fk_medication_id: string;
  monthly_max_quantity: number;
  applies_to: string;
  active: boolean;
  created_at: string | null;
}

interface DispatchExceptionResponse {
  id: string;
  fk_patient_id: string;
  fk_medication_id: string;
  authorized_quantity: number;
  valid_from: string;
  valid_until: string;
  reason: string;
  authorized_by: string | null;
  created_at: string | null;
}
```

---

## Recetas

### 1. `GET /inventory/prescriptions` — Listar/buscar

| Param | Descripcion |
|-------|-------------|
| `appointment_id` | Buscar por cita |
| `prescription_number` | Buscar por numero |
| `patient_id` | Filtrar por paciente |
| `page`, `page_size` | Paginacion |

### 2. `GET /inventory/prescriptions/{id}` — Detalle

### 3. `POST /inventory/prescriptions` — Crear

Numero de receta autogenerado. **Body:** `PrescriptionCreate`

---

## Ordenes de Compra

### 4. `POST /inventory/purchase-orders/{order_id}/receive` — Recepcion

Registra recepcion de items, crea lotes automaticamente, actualiza stock.

```typescript
interface ReceivePurchaseOrderInput {
  items: {
    purchase_order_item_id: string;
    quantity_received: number;
    lot_number: string;
    expiration_date: string;     // YYYY-MM-DD
    unit_cost?: number | null;
  }[];
}
```

---

## Despachos (FEFO atomico)

### 5. `GET /inventory/dispatches/validate` — Validar despacho

**Query:** `prescription_id` (req), `patient_type?`

**Response:** `DispatchValidationResponse`

Valida: stock disponible (FEFO), limites mensuales, excepciones.

### 6. `POST /inventory/dispatches` — Ejecutar despacho

**Body:** `DispatchCreate` | **Response (201):** `DispatchResponse`

Descuenta stock atomicamente usando FEFO.

### 7. `POST /inventory/dispatches/{id}/cancel` — Cancelar y revertir stock

### 8. `GET /inventory/dispatches/{id}` — Detalle

### 9. `GET /inventory/dispatches/by-prescription/{prescription_id}`

### 10. `GET /inventory/dispatches/by-patient/{patient_id}` — Historial (paginado)

**Query:** `prescription_number?`, `status?`, `date_from?`, `date_to?`, `page`, `page_size`

---

## Limites de Despacho

### 11. `GET /inventory/dispatch-limits` — Listar (paginado)

### 12. `POST /inventory/dispatch-limits` — Crear

### 13. `PATCH /inventory/dispatch-limits/{id}` — Actualizar

---

## Excepciones de Despacho

### 14. `GET /inventory/dispatch-exceptions` — Listar (paginado)

### 15. `POST /inventory/dispatch-exceptions` — Crear

---

## Reportes

### 16. `GET /inventory/reports/stock` — Reporte de stock completo

### 17. `GET /inventory/reports/inventory-summary` — KPIs ejecutivos

### 18. `GET /inventory/reports/low-stock` — Stock bajo/critico

### 19. `GET /inventory/reports/expiration?threshold_days=90` — Lotes por vencer

### 20. `GET /inventory/reports/expiring-soon` — Agrupado 30/60/90 dias

### 21. `GET /inventory/reports/consumption?period=2026-03` — Consumo mensual

### 22. `GET /inventory/reports/movements?medication_id={id}` — Kardex (paginado)

**Query:** `medication_id` (req), `date_from?`, `date_to?`, `page`, `page_size`
