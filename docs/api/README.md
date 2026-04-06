# API Backend -- Centro Ambulatorio ULA (CAMIULA)

Backend desarrollado en **FastAPI** (Python 3.9+, async) con **Clean Architecture**.
El frontend SvelteKit consume todas las rutas a traves de `apiFetch()` y `apiFetchRaw()`.

---

## URL Base

```
http://localhost:8000/api
```

Todas las rutas documentadas son relativas a este prefijo.

---

## Autenticacion

Todos los endpoints (excepto login y register) requieren un **JWT Bearer Token** en el header:

```
Authorization: Bearer <access_token>
```

El token se obtiene via `POST /api/auth/login`. Expira segun la configuracion del servidor.

---

## Envelope Estandar

**Toda** respuesta sigue este formato:

```typescript
interface ApiEnvelope<T> {
  status: "success" | "error";
  message: string;
  data: T;
}
```

El frontend desenvuelve automaticamente el campo `data` con `apiFetch<T>()`.
Para acceder al envelope completo, usar `apiFetchRaw<T>()`.

### Respuesta paginada

Los listados paginados envuelven `data` con:

```typescript
interface PaginatedData<T> {
  items: T[];
  pagination: {
    total: number;      // Total de registros
    page: number;       // Pagina actual (1-indexed)
    page_size: number;  // Tamano de pagina
    pages: number;      // Total de paginas
  };
}
```

Query params de paginacion:

| Parametro   | Tipo   | Default | Descripcion             |
|-------------|--------|---------|-------------------------|
| `page`      | number | 1       | Numero de pagina (base 1) |
| `page_size` | number | 20      | Cantidad de elementos por pagina (max 100) |

---

## Codigos de Estado HTTP

| Codigo | Significado | Uso |
|--------|-------------|-----|
| `200`  | OK | Operacion exitosa (GET, PUT, PATCH, DELETE) |
| `201`  | Created | Recurso creado exitosamente (POST) |
| `400`  | Bad Request | Datos de entrada invalidos o regla de negocio violada |
| `401`  | Unauthorized | Token faltante, invalido o expirado |
| `403`  | Forbidden | Token valido pero sin permiso para la accion |
| `404`  | Not Found | Recurso no encontrado |
| `409`  | Conflict | Conflicto de unicidad (cedula duplicada, RIF duplicado) |
| `422`  | Unprocessable | Validacion Pydantic fallida (campo faltante/tipo incorrecto) |
| `500`  | Internal Server Error | Error inesperado del servidor |

En caso de error, el body sigue el mismo envelope:

```json
{
  "status": "error",
  "message": "Descripcion del error legible para el desarrollador",
  "data": null
}
```

---

## Formato de Fechas

| Tipo | Formato | Ejemplo |
|------|---------|---------|
| Fecha | ISO 8601 `YYYY-MM-DD` | `2026-04-02` |
| Timestamp | ISO 8601 completo | `2026-04-02T14:30:00` |
| Hora | `HH:MM` (24h) | `08:30` |

---

## Convencion de Nombres

- **snake_case** para todos los campos JSON
- Prefijo **`fk_`** para llaves foraneas (`fk_patient_id`, `fk_doctor_id`)
- IDs como **string UUID** (`"550e8400-e29b-41d4-a716-446655440000"`)

---

## Indice de Documentacion por Modulo

| # | Documento | Modulo | Endpoints |
|---|-----------|--------|-----------|
| 1 | [01-auth.md](./01-auth.md) | Autenticacion y Usuarios (JWT + RBAC) | 9 |
| 2 | [02-patients.md](./02-patients.md) | Gestion de Pacientes | 6 |
| 3 | [03-appointments.md](./03-appointments.md) | Citas Medicas y Agendamiento | 9 |
| 4 | [04-doctors.md](./04-doctors.md) | Doctores, Especialidades y Disponibilidad | 12 |
| 5 | [05-medical-records.md](./05-medical-records.md) | Historias Medicas y Schemas Dinamicos | 10 |
| 6 | [06-inventory.md](./06-inventory.md) | Inventario: Medicamentos, Proveedores, Lotes | 13 |
| 7 | [07-pharmacy.md](./07-pharmacy.md) | Farmacia: Recetas, Despachos, Limites | 16 |
| 8 | [08-dashboard.md](./08-dashboard.md) | Dashboard BI: Metricas Consolidadas | 1 |
| 9 | [09-patient-portal.md](./09-patient-portal.md) | Portal del Paciente | 4 |

**Total: 82 endpoints**

---

## Flags de Mock (Migracion Progresiva)

El frontend opera en modo mock por defecto. Cuando un modulo del backend este listo,
establecer la variable de entorno a `false` en `.env`:

```env
MOCK_PACIENTES=false
MOCK_DOCTORES=false
MOCK_CITAS=false
# ... etc
```

| # | Variable de Entorno | Modulo |
|---|--------------------|--------------------|
| 1 | `MOCK_PACIENTES` | Pacientes |
| 2 | `MOCK_DOCTORES` | Doctores y Especialidades |
| 3 | `MOCK_CITAS` | Citas Medicas |
| 4 | `MOCK_HISTORIAS` | Historias Clinicas |
| 5 | `MOCK_SCHEMAS` | Schemas de Formularios |
| 6 | `MOCK_INVENTORY_MEDICATIONS` | Medicamentos |
| 7 | `MOCK_INVENTORY_SUPPLIERS` | Proveedores |
| 8 | `MOCK_INVENTORY_PURCHASE_ORDERS` | Ordenes de Compra |
| 9 | `MOCK_INVENTORY_BATCHES` | Lotes |
| 10 | `MOCK_INVENTORY_PRESCRIPTIONS` | Recetas |
| 11 | `MOCK_INVENTORY_DISPATCHES` | Despachos |
| 12 | `MOCK_INVENTORY_LIMITS` | Limites de Despacho |
| 13 | `MOCK_INVENTORY_REPORTS` | Reportes de Inventario |
