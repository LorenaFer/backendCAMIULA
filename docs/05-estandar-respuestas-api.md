# Estándar de Respuestas API

## Regla Principal

**TODO endpoint de la API DEBE devolver respuestas con el formato envelope estándar.**

No se permite construir `JSONResponse`, diccionarios o cualquier respuesta manual que no use los helpers.

## Formato del Envelope

Toda respuesta JSON de la API sigue esta estructura:

```json
{
  "status": "success" | "error",
  "message": "Descripción legible para humanos",
  "data": T | null
}
```

- **`status`**: Solo puede ser `"success"` o `"error"`. Nunca `"ok"`, `"fail"`, `true`/`false`.
- **`message`**: Texto descriptivo de lo que ocurrió. Útil para mostrar en frontend o para debugging.
- **`data`**: El payload de datos. `null` en errores o cuando no hay datos que devolver.

## Helpers Disponibles

Importar desde `app.shared.schemas.responses`:

```python
from app.shared.schemas.responses import ok, created, error, paginated
```

### `ok(data, message, status_code)`

Respuesta exitosa genérica. HTTP 200 por defecto.

```python
@router.get("/patients/{patient_id}")
async def get_patient(patient_id: int, db: AsyncSession = Depends(get_session)):
    patient = await service.get_by_id(db, patient_id)
    if not patient:
        raise NotFoundException("Paciente no encontrado")
    return ok(data=patient.model_dump(), message="Paciente obtenido")
```

Respuesta:
```json
{
  "status": "success",
  "message": "Paciente obtenido",
  "data": {
    "id": 1,
    "name": "Juan Pérez",
    "cedula": "V-12345678"
  }
}
```

### `created(data, message)`

Para recursos recién creados. HTTP 201 automáticamente.

```python
@router.post("/patients", status_code=201)
async def create_patient(payload: PatientCreate, db: AsyncSession = Depends(get_session)):
    new_patient = await service.create(db, payload)
    return created(data=new_patient.model_dump(), message="Paciente registrado")
```

Respuesta:
```json
{
  "status": "success",
  "message": "Paciente registrado",
  "data": {
    "id": 5,
    "name": "María López",
    "cedula": "V-87654321"
  }
}
```

### `error(message, status_code, data)`

Para errores controlados desde el endpoint. HTTP 400 por defecto.

```python
@router.post("/patients")
async def create_patient(payload: PatientCreate, db: AsyncSession = Depends(get_session)):
    if await service.exists_by_cedula(db, payload.cedula):
        return error(message="Ya existe un paciente con esa cédula", status_code=409)
    # ...
```

Respuesta:
```json
{
  "status": "error",
  "message": "Ya existe un paciente con esa cédula",
  "data": null
}
```

> **Nota:** Para la mayoría de errores, preferir `raise AppException(...)` / `raise NotFoundException(...)` en lugar de `error()`. Las excepciones son manejadas automáticamente por el error handler global y devuelven el mismo formato estándar.

### `paginated(items, total, page, page_size, message)`

Para listados con paginación.

```python
@router.get("/patients")
async def list_patients(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_session),
):
    items, total = await service.list_paginated(db, page=page, page_size=page_size)
    return paginated(
        items=[p.model_dump() for p in items],
        total=total,
        page=page,
        page_size=page_size,
        message="Listado de pacientes",
    )
```

Respuesta:
```json
{
  "status": "success",
  "message": "Listado de pacientes",
  "data": {
    "items": [
      {"id": 1, "name": "Juan Pérez"},
      {"id": 2, "name": "María López"}
    ],
    "pagination": {
      "total": 45,
      "page": 1,
      "page_size": 20,
      "pages": 3
    }
  }
}
```

## Manejo de Errores

### Excepciones de Dominio (preferido)

Usar las excepciones definidas en `app/core/exceptions.py`. El error handler global las convierte automáticamente al formato estándar:

```python
from app.core.exceptions import NotFoundException, ConflictException, AppException

# 404 - Recurso no encontrado
raise NotFoundException("Paciente no encontrado")

# 409 - Conflicto
raise ConflictException("Ya existe un paciente con esa cédula")

# 400 - Error genérico (o cualquier código)
raise AppException("Datos inválidos", status_code=422)
```

Todas producen el envelope estándar:
```json
{
  "status": "error",
  "message": "Paciente no encontrado",
  "data": null
}
```

### Errores no controlados

Si ocurre una excepción no manejada (bug, error de BD, etc.), el `generic_exception_handler` devuelve:

```json
{
  "status": "error",
  "message": "Error interno del servidor",
  "data": null
}
```

## Lo que NUNCA debes hacer

### 1. Construir JSONResponse manualmente en un endpoint

```python
# MAL
from fastapi.responses import JSONResponse

@router.get("/patients/{id}")
async def get_patient(id: int):
    return JSONResponse(status_code=200, content={"data": patient})

# BIEN
from app.shared.schemas.responses import ok

@router.get("/patients/{id}")
async def get_patient(id: int):
    return ok(data=patient.model_dump())
```

### 2. Devolver diccionarios con formato propio

```python
# MAL
@router.get("/patients/{id}")
async def get_patient(id: int):
    return {"success": True, "patient": patient}

# BIEN
@router.get("/patients/{id}")
async def get_patient(id: int):
    return ok(data=patient.model_dump())
```

### 3. Usar `raise HTTPException` en módulos

```python
# MAL — no pasa por nuestro error handler
from fastapi import HTTPException
raise HTTPException(status_code=404, detail="Not found")

# BIEN — usa nuestras excepciones que sí cumplen el estándar
from app.core.exceptions import NotFoundException
raise NotFoundException("Paciente no encontrado")
```

### 4. Inventar campos de status

```python
# MAL
return {"status": "ok", "result": data}
return {"error": True, "msg": "falló"}
return {"success": False, "detail": "no encontrado"}

# BIEN — solo "success" y "error" son válidos
return ok(data=data)
return error(message="no encontrado", status_code=404)
```

## Schemas Pydantic para Documentación

Para que los endpoints aparezcan correctamente en Swagger/OpenAPI, se pueden usar los schemas de `app/shared/schemas/common.py`:

```python
from app.shared.schemas.common import StandardResponse, PaginatedData, PaginationMeta
```

- `StandardResponse[T]` — para `response_model` en endpoints simples
- `PaginatedData[T]` — para el tipo de `data` en respuestas paginadas

> **Nota:** Dado que los helpers devuelven `JSONResponse`, el `response_model` en el decorador del endpoint es opcional pero recomendado para documentación.

## Resumen Rápido

| Acción | Helper / Excepción |
|--------|---------------------|
| Devolver datos (200) | `ok(data=..., message="...")` |
| Recurso creado (201) | `created(data=..., message="...")` |
| Listado paginado (200) | `paginated(items=..., total=..., page=..., page_size=...)` |
| Error de validación (400) | `raise AppException("mensaje")` |
| No encontrado (404) | `raise NotFoundException("mensaje")` |
| No autorizado (401) | `raise UnauthorizedException("mensaje")` |
| Conflicto (409) | `raise ConflictException("mensaje")` |
| Error controlado en endpoint | `error(message="...", status_code=...)` |
