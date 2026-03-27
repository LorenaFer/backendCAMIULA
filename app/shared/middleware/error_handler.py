from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.exceptions import AppException


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Convierte AppException al envelope estándar de error.

    Cuando la excepción tiene un campo `code` (ej. LIMIT_EXCEEDED),
    se incluye en el cuerpo junto con el campo `detail` para compatibilidad
    con el frontend que discrimina errores de negocio por código.
    """
    body: dict = {
        "status": "error",
        "message": exc.message,
        "data": None,
    }
    if exc.code:
        body["code"] = exc.code
        body["detail"] = exc.message
    return JSONResponse(status_code=exc.status_code, content=body)


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all para excepciones no controladas — mantiene el envelope."""
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "Error interno del servidor",
            "data": None,
        },
    )
