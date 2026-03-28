from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.exceptions import AppException
from app.shared.schemas.responses import error


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Convierte AppException al envelope estándar de error.

    Cuando la excepción tiene un campo `code` (ej. LIMIT_EXCEEDED),
    se incluye en el cuerpo para que el frontend discrimine errores de negocio.
    """
    body: dict = {
        "status": "error",
        "message": exc.message,
        "data": None,
    }
    if exc.code:
        body["code"] = exc.code
    return JSONResponse(status_code=exc.status_code, content=body)


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Convierte errores de validación Pydantic (422) al envelope estándar."""
    errors = []
    for err in exc.errors():
        field = " → ".join(str(loc) for loc in err["loc"] if loc != "body")
        errors.append({"field": field, "message": err["msg"]})

    return error(message="Error de validación", status_code=422, data=errors)


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all para excepciones no controladas — mantiene el envelope."""
    return error(message="Error interno del servidor", status_code=500)
