from typing import Any, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


# ---------------------------------------------------------------------------
# Envelope: every API response uses { "status", "message", "data" }
# ---------------------------------------------------------------------------


class StandardResponse(BaseModel, Generic[T]):
    """Standard response envelope for all API endpoints."""

    status: str = Field(description="Result status: 'success' or 'error'", example="success")
    message: str = Field(description="Human-readable result message", example="Operation completed successfully")
    data: Optional[T] = Field(None, description="Response payload (type varies by endpoint)")


class PaginationMeta(BaseModel):
    """Pagination metadata included in paginated responses."""

    total: int = Field(description="Total number of records matching the query", example=150)
    page: int = Field(description="Current page number (1-based)", example=1)
    page_size: int = Field(description="Number of items per page", example=20)
    pages: int = Field(description="Total number of pages", example=8)


class PaginatedData(BaseModel, Generic[T]):
    """Paginated response payload."""

    items: List[T] = Field(description="Array of items for the current page")
    pagination: PaginationMeta = Field(description="Pagination metadata")


class ValidationErrorDetail(BaseModel):
    """Detail of a single validation error."""

    field: str = Field(description="Field that failed validation", example="email")
    message: str = Field(description="Validation error message", example="Invalid email format")


class ErrorResponse(BaseModel):
    """Standard error response envelope (includes 422 validation errors)."""

    status: str = Field(default="error", description="Always 'error' for error responses", example="error")
    message: str = Field(description="Error description", example="Error de validacion")
    data: Optional[List[ValidationErrorDetail]] = Field(None, description="Validation error details (only for 422)")


# Alias (backward compat)
class MessageResponse(BaseModel):
    message: str = Field(description="Response message", example="OK")
