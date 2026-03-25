"""
Helpers estándar de respuesta API.

Todo endpoint DEBE usar estos helpers en lugar de construir JSONResponse
o diccionarios manualmente.  Esto garantiza el envelope uniforme:

    { "status": "success"|"error", "message": "...", "data": ... }

Uso en un router:

    from app.shared.schemas.responses import ok, created, error, paginated

    @router.get("/patients/{patient_id}")
    async def get_patient(...):
        patient = await service.get_by_id(db, patient_id)
        if not patient:
            raise NotFoundException("Paciente no encontrado")
        return ok(data=patient.model_dump(), message="Paciente obtenido")

    @router.post("/patients", status_code=201)
    async def create_patient(...):
        new = await service.create(db, payload)
        return created(data=new.model_dump(), message="Paciente creado")
"""

from typing import Any, Optional

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse


# ---------- Success helpers ----------


def ok(
    data: Any = None,
    message: str = "OK",
    status_code: int = 200,
) -> JSONResponse:
    """Respuesta exitosa genérica (200 por defecto)."""
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "success",
            "message": message,
            "data": jsonable_encoder(data),
        },
    )


def created(
    data: Any = None,
    message: str = "Recurso creado exitosamente",
) -> JSONResponse:
    """Respuesta de creación exitosa (HTTP 201)."""
    return ok(data=data, message=message, status_code=201)


# ---------- Error helper ----------


def error(
    message: str = "Error",
    status_code: int = 400,
    data: Any = None,
) -> JSONResponse:
    """Respuesta de error."""
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "error",
            "message": message,
            "data": jsonable_encoder(data) if data is not None else None,
        },
    )


# ---------- Pagination helper ----------


def paginated(
    items: list,
    total: int,
    page: int,
    page_size: int,
    message: str = "OK",
) -> JSONResponse:
    """Respuesta paginada estándar.

    Calcula automáticamente el número total de páginas y has_next.
    """
    pages = -(-total // page_size) if page_size > 0 else 0
    return ok(
        data={
            "items": jsonable_encoder(items),
            "pagination": {
                "total": total,
                "page": page,
                "page_size": page_size,
                "pages": pages,
                "has_next": page < pages,
            },
        },
        message=message,
    )
