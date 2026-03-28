from typing import Any, Generic, List, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


# ---------------------------------------------------------------------------
# Envelope estándar: toda respuesta JSON de la API usa este formato
# { "status": "success" | "error", "message": "...", "data": T | null }
# ---------------------------------------------------------------------------


class StandardResponse(BaseModel, Generic[T]):
    """Envelope genérico para respuestas exitosas y de error."""

    status: str
    message: str
    data: Optional[T] = None


class PaginationMeta(BaseModel):
    """Metadatos de paginación."""

    total: int
    page: int
    page_size: int
    pages: int


class PaginatedData(BaseModel, Generic[T]):
    """Payload de respuesta paginada."""

    items: List[T]
    pagination: PaginationMeta


class ValidationErrorDetail(BaseModel):
    """Detalle de un error de validación."""

    field: str
    message: str


class ErrorResponse(BaseModel):
    """Envelope estándar para errores (incluye 422)."""

    status: str = "error"
    message: str
    data: Optional[List[ValidationErrorDetail]] = None


# Alias de conveniencia (retrocompatible con el health check original)
class MessageResponse(BaseModel):
    message: str
