# Guía de Integración API — CAMIULA Backend

**Versión:** 1.0
**Módulo cubierto:** Inventario Farmacéutico
**Autor:** Julio Vasquez 

---

## Tabla de Contenidos

1. [Configuración Global](#1-configuración-global)
2. [Formato Estándar de Respuesta](#2-formato-estándar-de-respuesta)
3. [Códigos de Error de Negocio](#3-códigos-de-error-de-negocio)
4. [Catálogo de Endpoints](#4-catálogo-de-endpoints)
   - [Medicamentos](#41-medicamentos)
   - [Despachos](#42-despachos)
   - [Reportes y Analytics](#43-reportes-y-analytics)
   - [Stubs pendientes de implementación](#44-stubs-pendientes-de-implementación)
5. [Mapeo de Modelos: TypeScript ↔ Pydantic](#5-mapeo-de-modelos-typescript--pydantic)
6. [Flujos Críticos](#6-flujos-críticos)
   - [Flujo de Despacho FEFO](#61-flujo-de-despacho-fefo)
   - [Flujo de Cancelación de Despacho](#62-flujo-de-cancelación-de-despacho)
7. [Notas de Desarrollo](#7-notas-de-desarrollo)

---

## 1. Configuración Global

### Base URL

| Entorno     | URL                                |
|-------------|------------------------------------|
| Desarrollo  | `http://localhost:8000/api`        |
| Producción  | `https://api.camiula.ula.ve/api`   |

El cliente HTTP ya lo maneja en `src/lib/server/api.ts` vía la variable de entorno `API_URL`. Todos los paths de este documento asumen que el prefijo `/api` ya está incluido en `API_URL` **o** que los paths se prefijan con `/api`.

**Ejemplo:**

```
GET http://localhost:8000/api/inventory/medications
```

### Headers Obligatorios

| Header          | Valor                         | Requerido        |
|-----------------|-------------------------------|------------------|
| `Content-Type`  | `application/json`            | Siempre          |
| `Authorization` | `Bearer <access_token>`       | Todos excepto `/api/health` |

El cliente `apiFetch` ya inyecta `Content-Type: application/json`. Lo que **falta agregar** es el header de autorización para las rutas autenticadas.

```typescript
// src/lib/server/api.ts — integración del token
export async function apiFetch<T>(path: string, init?: RequestInit, token?: string): Promise<T> {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...init?.headers,
  };
  // ...
}
```

### Autenticación — JWT Bearer

El backend valida el token con `HS256`. El payload del JWT contiene:

```json
{
  "sub": "<user_id>",
  "exp": 1750000000
}
```

- `sub` es el identificador del usuario autenticado (farmacéutico, médico, etc.).
- El token expira en **30 minutos** por defecto (configurable vía `.env`).
- Si el token es inválido o expirado, el backend responde con `HTTP 401`.

### CORS

En desarrollo, el backend acepta peticiones desde cualquier origen (`allow_origins: ["*"]`). En producción se deberá restringir al dominio del frontend.

### Timeout

El cliente `apiFetch` del frontend ya incluye un timeout de **15 segundos** con `AbortController`. No se requiere configuración adicional.

---

## 2. Formato Estándar de Respuesta

**Todo endpoint** devuelve el siguiente envelope. Nunca se retorna el objeto de negocio directamente en el body raíz.

### Respuesta exitosa (singular)

```json
{
  "status": "success",
  "message": "Medicamento obtenido exitosamente",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "code": "AMX-500",
    "generic_name": "Amoxicilina 500mg"
  }
}
```

### Respuesta exitosa paginada

```json
{
  "status": "success",
  "message": "Medicamentos obtenidos exitosamente",
  "data": {
    "items": [ /* ... array de objetos */ ],
    "pagination": {
      "total": 42,
      "page": 1,
      "page_size": 20,
      "pages": 3
    }
  }
}
```

### Respuesta de error general

```json
{
  "status": "error",
  "message": "Receta no encontrada",
  "data": null
}
```

### Respuesta de error de negocio (con `code`)

Cuando el error corresponde a una regla de negocio identificable por el frontend (por ejemplo, para mostrar un mensaje específico o cambiar el estado de la UI), el body incluye además `code` y `detail`:

```json
{
  "status": "error",
  "message": "Límite mensual excedido: 42 usados + 42 solicitados > 42 permitidos",
  "data": null,
  "code": "LIMIT_EXCEEDED",
  "detail": "Límite mensual excedido: 42 usados + 42 solicitados > 42 permitidos"
}
```

> **Para el frontend:** discriminar el tipo de error de negocio usando `body.code`, no `body.message` (el mensaje puede cambiar). El campo `detail` es un alias de `message` incluido por compatibilidad.

---

## 3. Códigos de Error de Negocio

| Código                | HTTP | Descripción                                                    |
|-----------------------|------|----------------------------------------------------------------|
| `LIMIT_EXCEEDED`      | 403  | La cantidad solicitada supera el límite mensual del paciente   |
| `INSUFFICIENT_STOCK`  | 409  | No hay unidades disponibles en los lotes activos               |
| `INVALID_STATUS`      | 403  | La receta o despacho está en un estado que impide la operación |
| `NOTHING_TO_DISPATCH` | 403  | Todos los ítems de la receta ya fueron despachados o cancelados |
| `ALREADY_CANCELLED`   | 403  | El despacho ya se encuentra cancelado                          |
| `FORBIDDEN`           | 403  | Operación no permitida (genérico)                              |

---

## 4. Catálogo de Endpoints

> **Convención:** todos los paths son relativos a `BASE_URL`. Por ejemplo, `/inventory/medications` equivale a `http://localhost:8000/api/inventory/medications`.

---

### 4.1 Medicamentos

#### Listar medicamentos (con filtros y paginación)

```
GET /inventory/medications
```

**Query params:**

| Parámetro          | Tipo   | Por defecto | Descripción                             |
|--------------------|--------|-------------|-----------------------------------------|
| `search`           | string | —           | Búsqueda parcial en `generic_name`      |
| `status`           | string | —           | `active` \| `discontinued` \| `pending` |
| `therapeutic_class`| string | —           | Filtro exacto por clase terapéutica     |
| `page`             | int    | `1`         | Página (≥ 1)                            |
| `page_size`        | int    | `20`        | Registros por página (1-100)            |

**Respuesta `200`:** paginada con items de tipo `Medication`.

```json
{
  "status": "success",
  "message": "Medicamentos obtenidos exitosamente",
  "data": {
    "items": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440001",
        "code": "AMX-500",
        "generic_name": "Amoxicilina 500mg",
        "commercial_name": null,
        "pharmaceutical_form": "Cápsulas",
        "concentration": "500mg",
        "unit_measure": "cápsulas",
        "therapeutic_class": "Antibiótico",
        "controlled_substance": false,
        "requires_refrigeration": false,
        "medication_status": "active",
        "current_stock": 300,
        "created_at": "2026-03-01T00:00:00+00:00"
      }
    ],
    "pagination": { "total": 3, "page": 1, "page_size": 20, "pages": 1 }
  }
}
```

---

#### Lista simplificada para `<select>` (dropdowns)

```
GET /inventory/medications/options
```

No recibe parámetros. Devuelve solo los campos necesarios para selectores:

```json
{
  "status": "success",
  "data": [
    {
      "id": "550e8400-...",
      "code": "AMX-500",
      "generic_name": "Amoxicilina 500mg",
      "pharmaceutical_form": "Cápsulas",
      "unit_measure": "cápsulas",
      "current_stock": 300
    }
  ]
}
```

---

#### Detalle de medicamento

```
GET /inventory/medications/{id}
```

Incluye el `current_stock` calculado en tiempo real (suma de lotes disponibles no vencidos).

---

#### Crear medicamento

```
POST /inventory/medications
```

**Body:**

```json
{
  "code": "IBU-600",
  "generic_name": "Ibuprofeno 600mg",
  "pharmaceutical_form": "Comprimidos",
  "unit_measure": "comprimidos",
  "controlled_substance": false,
  "requires_refrigeration": false,
  "commercial_name": null,
  "concentration": "600mg",
  "therapeutic_class": "Antiinflamatorio"
}
```

**Respuesta `201`:** objeto `Medication` completo.

---

#### Actualizar medicamento

```
PUT /inventory/medications/{id}
```

Todos los campos son opcionales. Solo se actualizan los campos enviados.

---

#### Eliminar medicamento (soft-delete)

```
DELETE /inventory/medications/{id}
```

Marca el registro como inactivo (`status = 'I'`). No elimina físicamente.

---

### 4.2 Despachos

#### Validar despacho (pre-vuelo)

```
GET /inventory/dispatches/validate
```

**⚠ Llamar siempre antes de `POST /dispatches`.** Este endpoint es de solo lectura y no modifica el estado de la base de datos. Devuelve el análisis completo de viabilidad por ítem.

**Query params:**

| Parámetro         | Tipo   | Requerido | Descripción                                         |
|-------------------|--------|-----------|-----------------------------------------------------|
| `prescription_id` | string | ✓         | ID de la receta a despachar                         |
| `patient_type`    | string | —         | `all` (defecto) \| `student` \| `employee` \| `professor` |

**Respuesta `200`:**

```json
{
  "status": "success",
  "message": "Validación completada",
  "data": {
    "can_dispatch": true,
    "prescription_id": "rx-uuid-001",
    "patient_id": "patient-uuid-001",
    "items": [
      {
        "medication_id": "med-uuid-001",
        "generic_name": "Amoxicilina 500mg",
        "quantity_prescribed": 42,
        "quantity_available": 300,
        "monthly_limit": 42,
        "monthly_used": 0,
        "monthly_remaining": 42,
        "has_exception": false,
        "can_dispatch": true,
        "block_reason": null
      }
    ]
  }
}
```

**Cuando `can_dispatch: false`:**

```json
{
  "data": {
    "can_dispatch": false,
    "items": [
      {
        "can_dispatch": false,
        "block_reason": "Límite mensual excedido: 42 usados + 42 solicitados > 42 permitidos",
        "has_exception": false
      }
    ]
  }
}
```

> La UI debe revisar `data.can_dispatch` primero. Si es `false`, mostrar `block_reason` del ítem correspondiente. Si `has_exception: true`, puede despacharse de todas formas dentro de la cantidad autorizada.

---

#### Ejecutar despacho (FEFO atómico)

```
POST /inventory/dispatches
```

El backend aplica automáticamente la estrategia FEFO (First Expired, First Out): consume primero los lotes con la fecha de vencimiento más próxima. **No es necesario que el frontend seleccione lotes manualmente.**

**Body:**

```json
{
  "fk_prescription_id": "rx-uuid-001",
  "patient_type": "all",
  "notes": "Despacho parcial — paciente retiró 42 cápsulas"
}
```

| Campo                | Tipo   | Requerido | Descripción                                                  |
|----------------------|--------|-----------|--------------------------------------------------------------|
| `fk_prescription_id` | string | ✓         | ID de la receta                                              |
| `patient_type`       | string | —         | Tipo de beneficiario para validar límite (`all` por defecto) |
| `notes`              | string | —         | Observaciones opcionales (máx. 500 caracteres)               |

**Respuesta `201`:**

```json
{
  "status": "success",
  "message": "Despacho ejecutado exitosamente",
  "data": {
    "id": "dispatch-uuid-001",
    "fk_prescription_id": "rx-uuid-001",
    "fk_patient_id": "patient-uuid-001",
    "fk_pharmacist_id": "pharmacist-uuid-001",
    "dispatch_date": "2026-03-27T14:35:00+00:00",
    "dispatch_status": "completed",
    "notes": null,
    "items": [
      {
        "id": "di-uuid-001",
        "fk_batch_id": "batch-near-uuid",
        "fk_medication_id": "med-uuid-001",
        "quantity_dispatched": 42
      }
    ],
    "created_at": "2026-03-27T14:35:00+00:00"
  }
}
```

**Errores posibles:**

| Código               | Causa                                              |
|----------------------|----------------------------------------------------|
| `LIMIT_EXCEEDED`     | Límite mensual superado sin excepción activa       |
| `INSUFFICIENT_STOCK` | No hay stock disponible para cubrir la prescripción|
| `INVALID_STATUS`     | La receta ya fue despachada o cancelada            |
| `NOTHING_TO_DISPATCH`| Todos los ítems ya fueron dispensados              |

---

#### Cancelar despacho

```
POST /inventory/dispatches/{id}/cancel
```

Revierte el stock en los lotes afectados y recalcula el estado de la receta.
**No admite body.**

**Respuesta `200`:**

```json
{
  "status": "success",
  "message": "Despacho cancelado y stock revertido exitosamente",
  "data": null
}
```

---

#### Obtener despacho por ID

```
GET /inventory/dispatches/{id}
```

---

#### Despachos de una receta

```
GET /inventory/dispatches/by-prescription/{prescription_id}
```

Devuelve un array (no paginado) con todos los despachos activos de la receta indicada.

---

#### Historial de despachos de un paciente

```
GET /inventory/dispatches/by-patient/{patient_id}
```

**Query params:**

| Parámetro             | Tipo   | Descripción                                 |
|-----------------------|--------|---------------------------------------------|
| `prescription_number` | string | Filtrar por número de receta                |
| `status`              | string | `pending` \| `completed` \| `cancelled`     |
| `date_from`           | string | ISO date `YYYY-MM-DD` (inclusive)           |
| `date_to`             | string | ISO date `YYYY-MM-DD` (inclusive)           |
| `page`                | int    | Página (defecto `1`)                        |
| `page_size`           | int    | Registros por página (defecto `20`, máx `100`) |

---

### 4.3 Reportes y Analytics

#### Reporte de stock consolidado ← *Dashboard principal*

```
GET /inventory/reports/stock
```

Este endpoint es el que carga el dashboard principal de inventario. Consolida el stock vigente por medicamento considerando solo lotes no vencidos con `batch_status = 'available'`.

**Respuesta `200`:**

```json
{
  "status": "success",
  "data": {
    "generated_at": "2026-03-27T14:00:00+00:00",
    "total_medications": 3,
    "critical_count": 0,
    "expired_count": 0,
    "items": [
      {
        "medication_id": "med-uuid-001",
        "code": "AMX-500",
        "generic_name": "Amoxicilina 500mg",
        "pharmaceutical_form": "Cápsulas",
        "unit_measure": "cápsulas",
        "total_available": 300,
        "batch_count": 2,
        "nearest_expiration": "2026-05-15",
        "days_to_expiration": 49,
        "stock_alert": "ok"
      }
    ]
  }
}
```

**Lógica de `stock_alert`:**

| Valor      | Condición                              |
|------------|----------------------------------------|
| `expired`  | `total_available == 0`                 |
| `critical` | `0 < total_available ≤ 10`             |
| `low`      | `10 < total_available ≤ 50`            |
| `ok`       | `total_available > 50`                 |

> Los umbrales están definidos en `app/modules/inventory/application/dtos/report_dto.py` como constantes `STOCK_THRESHOLD_CRITICAL = 10` y `STOCK_THRESHOLD_LOW = 50`. Si se requiere ajustarlos, es el único lugar donde hacerlo.

---

#### KPIs ejecutivos

```
GET /inventory/reports/inventory-summary
```

```json
{
  "data": {
    "generated_at": "2026-03-27T14:00:00+00:00",
    "total_active_skus": 3,
    "critical_count": 0,
    "low_count": 0,
    "expired_count": 0,
    "total_available_units": 560
  }
}
```

---

#### Stock bajo / crítico

```
GET /inventory/reports/low-stock
```

Devuelve solo los medicamentos con `stock_alert` en `low`, `critical` o `expired`, ordenados de más a menos grave.

```json
{
  "data": {
    "generated_at": "2026-03-27T14:00:00+00:00",
    "items": [ /* StockItem con stock_alert != 'ok' */ ],
    "total": 2
  }
}
```

---

#### Lotes próximos a vencer ← *Página de Batches*

```
GET /inventory/reports/expiration?threshold_days=90
```

**Query params:**

| Parámetro        | Por defecto | Rango   | Descripción                               |
|------------------|-------------|---------|-------------------------------------------|
| `threshold_days` | `90`        | 1 – 365 | Días a partir de hoy como horizonte       |

Cada lote incluye el objeto `medication` embebido:

```json
{
  "data": {
    "generated_at": "2026-03-27T14:00:00+00:00",
    "threshold_days": 90,
    "batches": [
      {
        "id": "batch-uuid-001",
        "fk_medication_id": "med-uuid-001",
        "medication": {
          "id": "med-uuid-001",
          "code": "AMX-500",
          "generic_name": "Amoxicilina 500mg",
          "pharmaceutical_form": "Cápsulas",
          "unit_measure": "cápsulas",
          "current_stock": 300
        },
        "lot_number": "LOT-2026-AMX-001",
        "expiration_date": "2026-05-15",
        "quantity_available": 100,
        "quantity_received": 100,
        "batch_status": "available",
        "received_at": "2026-01-10",
        "unit_cost": null
      }
    ]
  }
}
```

---

#### Lotes próximos a vencer (agrupados 30/60/90 días)

```
GET /inventory/reports/expiring-soon
```

Sin parámetros. Clasifica los lotes que vencen en los próximos 90 días en tres grupos:

```json
{
  "data": {
    "generated_at": "...",
    "vencen_en_30": [ /* lotes que vencen en ≤ 30 días */ ],
    "vencen_en_60": [ /* lotes entre 31 y 60 días */ ],
    "vencen_en_90": [ /* lotes entre 61 y 90 días */ ],
    "total": 1
  }
}
```

---

#### Consumo mensual por medicamento

```
GET /inventory/reports/consumption?period=2026-03
```

**Query params:**

| Parámetro | Formato  | Requerido | Descripción                  |
|-----------|----------|-----------|------------------------------|
| `period`  | `YYYY-MM`| ✓         | Mes a analizar               |

```json
{
  "data": {
    "period": "2026-03",
    "items": [
      {
        "medication_id": "med-uuid-001",
        "generic_name": "Amoxicilina 500mg",
        "total_dispatched": 84,
        "dispatch_count": 2,
        "patient_count": 2
      }
    ]
  }
}
```

Si no hay despachos en el período, `items` es `[]`.

---

#### Kardex / Movimientos

```
GET /inventory/reports/movements?medication_id={id}
```

Combina entradas (lotes recibidos) y salidas (ítems despachados) de un medicamento en orden cronológico inverso.

**Query params:**

| Parámetro       | Requerido | Descripción                              |
|-----------------|-----------|------------------------------------------|
| `medication_id` | ✓         | ID del medicamento                       |
| `date_from`     | —         | ISO date `YYYY-MM-DD`                    |
| `date_to`       | —         | ISO date `YYYY-MM-DD`                    |
| `page`          | —         | Defecto `1`                              |
| `page_size`     | —         | Defecto `20`, máx `100`                  |

```json
{
  "data": {
    "medication_id": "med-uuid-001",
    "generic_name": "Amoxicilina 500mg",
    "items": [
      {
        "movement_date": "2026-03-27T14:35:00+00:00",
        "movement_type": "exit",
        "reference": "PRX-2026-0001",
        "lot_number": null,
        "quantity": 42,
        "unit_cost": null,
        "notes": null
      },
      {
        "movement_date": "2026-01-10T00:00:00",
        "movement_type": "entry",
        "reference": "OC-2026-001",
        "lot_number": "LOT-2026-AMX-001",
        "quantity": 100,
        "unit_cost": 1.5,
        "notes": null
      }
    ],
    "pagination": {
      "total": 2,
      "page": 1,
      "page_size": 20,
      "pages": 1
    }
  }
}
```

---

### 4.4 Stubs pendientes de implementación

Los siguientes módulos tienen el router registrado pero los endpoints aún no están implementados. Se completarán en fases posteriores.

| Prefijo                          | Estado   | Descripción                     |
|----------------------------------|----------|---------------------------------|
| `/inventory/suppliers`           | Pendiente | CRUD de proveedores             |
| `/inventory/batches`             | Pendiente | CRUD de lotes                   |
| `/inventory/purchase-orders`     | Pendiente | Órdenes de compra y recepción   |
| `/inventory/prescriptions`       | Pendiente | Recetas médicas                 |
| `/inventory/dispatch-limits`     | Pendiente | Límites y excepciones de despacho |

---

## 5. Mapeo de Modelos: TypeScript ↔ Pydantic

### Medication / MedicationResponse

| Campo TypeScript         | Campo Pydantic           | Tipo TS              | Tipo Python         | Notas                                    |
|--------------------------|--------------------------|----------------------|---------------------|------------------------------------------|
| `id`                     | `id`                     | `string`             | `str`               | UUID v4                                  |
| `code`                   | `code`                   | `string`             | `str`               | Único, máx 50 chars                      |
| `generic_name`           | `generic_name`           | `string`             | `str`               | Máx 200 chars                            |
| `commercial_name`        | `commercial_name`        | `string \| undefined`| `Optional[str]`     |                                          |
| `pharmaceutical_form`    | `pharmaceutical_form`    | `string`             | `str`               | Ej: `"Cápsulas"`, `"Comprimidos"`        |
| `concentration`          | `concentration`          | `string \| undefined`| `Optional[str]`     | Ej: `"500mg"`                            |
| `unit_measure`           | `unit_measure`           | `string`             | `str`               | Ej: `"cápsulas"`, `"ml"`                 |
| `therapeutic_class`      | `therapeutic_class`      | `string \| undefined`| `Optional[str]`     |                                          |
| `controlled_substance`   | `controlled_substance`   | `boolean`            | `bool`              |                                          |
| `requires_refrigeration` | `requires_refrigeration` | `boolean`            | `bool`              |                                          |
| `medication_status`      | `medication_status`      | `MedicationStatus`   | `str`               | `active` \| `discontinued` \| `pending`  |
| `current_stock`          | `current_stock`          | `number`             | `int`               | Calculado — suma de lotes no vencidos    |
| `created_at`             | `created_at`             | `string`             | `Optional[str]`     | ISO 8601                                 |

### Dispatch / DispatchResponse

| Campo TypeScript    | Campo Pydantic       | Notas                                        |
|---------------------|----------------------|----------------------------------------------|
| `id`                | `id`                 |                                              |
| `fk_prescription_id`| `fk_prescription_id` |                                              |
| `fk_patient_id`     | `fk_patient_id`      |                                              |
| `fk_pharmacist_id`  | `fk_pharmacist_id`   | El backend lo toma del JWT (`sub`)           |
| `dispatch_date`     | `dispatch_date`      | ISO 8601 con timezone                        |
| `dispatch_status`   | `dispatch_status`    | `pending` \| `completed` \| `cancelled`      |
| `notes`             | `notes`              |                                              |
| `items`             | `items`              | Array de `DispatchItem`                      |
| `created_at`        | `created_at`         |                                              |
| `prescription_number` | —                  | **No incluido** en response actual. Enriquecer en frontend si se necesita. |
| `patient_name`      | —                    | **No incluido.** Resolver en el módulo de Pacientes. |

### DispatchValidationItem / DispatchValidationItemDTO

| Campo TypeScript   | Campo Pydantic     | Notas                                                  |
|--------------------|--------------------|--------------------------------------------------------|
| `medication_id`    | `medication_id`    |                                                        |
| `generic_name`     | `generic_name`     |                                                        |
| `quantity_prescribed` | `quantity_prescribed` |                                                 |
| `quantity_available`  | `quantity_available`  | Stock total de lotes no vencidos                |
| `monthly_limit`    | `monthly_limit`    | `null` si no hay límite configurado                    |
| `monthly_used`     | `monthly_used`     | Despachos del mes en curso (excluye cancelados)        |
| `monthly_remaining`| `monthly_remaining`| `null` si no hay límite; `monthly_limit - monthly_used` si existe |
| `has_exception`    | `has_exception`    | `true` si existe una `DispatchException` activa        |
| `can_dispatch`     | `can_dispatch`     |                                                        |
| `block_reason`     | `block_reason`     | `null` cuando `can_dispatch: true`                     |

### StockItem (Reporte)

| Campo TypeScript      | Campo Pydantic        | Notas                                      |
|-----------------------|-----------------------|--------------------------------------------|
| `medication_id`       | `medication_id`       |                                            |
| `code`                | `code`                |                                            |
| `generic_name`        | `generic_name`        |                                            |
| `pharmaceutical_form` | `pharmaceutical_form` |                                            |
| `unit_measure`        | `unit_measure`        |                                            |
| `total_available`     | `total_available`     | Suma de lotes no vencidos con qty > 0      |
| `batch_count`         | `batch_count`         | Número de lotes activos no vencidos        |
| `nearest_expiration`  | `nearest_expiration`  | ISO date `YYYY-MM-DD` o `null`             |
| `days_to_expiration`  | `days_to_expiration`  | Entero o `null`                            |
| `stock_alert`         | `stock_alert`         | `ok` \| `low` \| `critical` \| `expired`  |

---

## 6. Flujos Críticos

### 6.1 Flujo de Despacho FEFO

El frontend debe seguir este orden estrictamente para garantizar una experiencia de usuario correcta y evitar errores en el backend.

```
┌─────────────────────────────────────────────────────────────────┐
│  PASO 1 — Obtener la receta                                     │
│  GET /inventory/prescriptions/{id}                              │
│  → Verificar prescription_status != 'dispensed' | 'cancelled'  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  PASO 2 — Validar viabilidad del despacho (solo lectura)        │
│  GET /inventory/dispatches/validate                             │
│    ?prescription_id={id}&patient_type={tipo}                   │
│                                                                 │
│  → Si data.can_dispatch == false:                               │
│      Mostrar block_reason del ítem bloqueado                    │
│      NO continuar al Paso 3                                     │
│                                                                 │
│  → Si data.can_dispatch == true:                                │
│      Mostrar resumen al farmacéutico y pedir confirmación       │
└────────────────────────────┬────────────────────────────────────┘
                             │ Farmacéutico confirma
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  PASO 3 — Ejecutar el despacho                                  │
│  POST /inventory/dispatches                                     │
│  Body: { fk_prescription_id, patient_type, notes? }            │
│                                                                 │
│  El backend aplica FEFO automáticamente.                        │
│  No enviar IDs de lote — el servidor los selecciona.            │
│                                                                 │
│  → HTTP 201: Mostrar comprobante con data.items                 │
│                                                                 │
│  → HTTP 403 + code == "LIMIT_EXCEEDED":                         │
│      Mostrar mensaje de límite (puede haberse agotado el límite │
│      entre el validate y el execute — condición de carrera)     │
│                                                                 │
│  → HTTP 409 + code == "INSUFFICIENT_STOCK":                     │
│      Stock agotado entre validate y execute — reintentar        │
│      validación desde Paso 2                                    │
└─────────────────────────────────────────────────────────────────┘
```

**Nota sobre condiciones de carrera:** entre el Paso 2 (validate) y el Paso 3 (execute) puede existir un intervalo de tiempo donde otro proceso consuma el stock o el límite mensual. El backend usa `SELECT FOR UPDATE` en la lectura de lotes dentro del execute para serializar el acceso concurrente, por lo que los errores `INSUFFICIENT_STOCK` y `LIMIT_EXCEEDED` en el execute son definitivos y deben manejarse en la UI.

---

### 6.2 Flujo de Cancelación de Despacho

```
┌─────────────────────────────────────────────────────────────────┐
│  PASO 1 — Cargar el despacho                                    │
│  GET /inventory/dispatches/{id}                                 │
│  → Verificar dispatch_status == 'completed'                     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  PASO 2 — Ejecutar cancelación                                  │
│  POST /inventory/dispatches/{id}/cancel                         │
│                                                                 │
│  El backend:                                                    │
│    1. Restaura quantity_available en cada lote afectado         │
│    2. Revierte quantity_dispatched en los ítems de la receta    │
│    3. Recalcula prescription_status                             │
│       (dispensed → partial → active según lo revertido)         │
│                                                                 │
│  → HTTP 200: Despacho cancelado                                 │
│  → HTTP 403 + code == "ALREADY_CANCELLED": ya estaba cancelado  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 7. Notas de Desarrollo

### Variable de entorno requerida en el frontend

```bash
# .env (frontend)
API_URL=http://localhost:8000
```

El path `/api` debe incluirse en cada llamada a `apiFetch`, no en `API_URL`. Ejemplo:

```typescript
// Correcto
apiFetch('/api/inventory/medications')

// Incorrecto — duplicaría el prefijo si API_URL ya incluyera /api
apiFetch('/inventory/medications')
```

### Manejo de errores con `code` en el cliente

```typescript
// src/lib/server/api.ts — patrón recomendado para errores de negocio
try {
  const result = await apiFetch<Dispatch>('/api/inventory/dispatches', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  // ...
} catch (err) {
  if (err instanceof ApiError) {
    const body = err.body as { code?: string; detail?: string; message?: string };

    if (body.code === 'LIMIT_EXCEEDED') {
      // Mostrar modal de límite excedido con body.detail
    } else if (body.code === 'INSUFFICIENT_STOCK') {
      // Mostrar alerta de stock agotado
    } else {
      // Error genérico
      console.error(body.message ?? 'Error desconocido');
    }
  }
}
```

### Formato de fechas

- **Fechas simples** (`expiration_date`, `received_at`, `prescription_date`): ISO `YYYY-MM-DD`.
- **Timestamps** (`dispatch_date`, `created_at`, `generated_at`): ISO 8601 con timezone `+00:00`.
- Los query params de fecha (`date_from`, `date_to`, `period`) siempre van en formato ISO como strings.

### Identificadores

Todos los `id` son **UUID v4** en formato string (`"550e8400-e29b-41d4-a716-446655440000"`). No existen IDs numéricos en este módulo.

### Paginación — comportamiento del servidor

- El servidor nunca devuelve más de `page_size` registros.
- Si `page` supera el total de páginas, `items` es `[]` (no se lanza error).
- `pagination.pages` es el techo de `total / page_size`.

### Campos enriquecidos que el backend NO devuelve

Los siguientes campos están definidos en las interfaces TypeScript del frontend pero **no son calculados por el backend** en su estado actual. Deben resolverse en el frontend o mediante llamadas adicionales a otros módulos:

| Interfaz        | Campo              | Resolver en                          |
|-----------------|--------------------|--------------------------------------|
| `Dispatch`      | `prescription_number` | GET /inventory/dispatches/by-prescription |
| `Dispatch`      | `patient_name`     | Módulo de Pacientes (pendiente)      |
| `Dispatch`      | `pharmacist_name`  | Módulo de Usuarios (pendiente)       |
| `Prescription`  | `patient_name`     | Módulo de Pacientes (pendiente)      |
| `Prescription`  | `doctor_name`      | Módulo de Usuarios (pendiente)       |
| `DispatchItem`  | `lot_number`       | GET /inventory/batches/{fk_batch_id} |
| `DispatchItem`  | `medication`       | GET /inventory/medications/options   |
| `DispatchLimit` | `medication`       | GET /inventory/medications/options   |
