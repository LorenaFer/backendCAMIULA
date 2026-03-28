from typing import Optional


class AppException(Exception):
    def __init__(self, message: str, status_code: int = 400, code: Optional[str] = None):
        self.message = message
        self.status_code = status_code
        self.code = code


class NotFoundException(AppException):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message=message, status_code=404)


class UnauthorizedException(AppException):
    def __init__(self, message: str = "Not authorized"):
        super().__init__(message=message, status_code=401)


class ConflictException(AppException):
    def __init__(self, message: str = "Resource already exists"):
        super().__init__(message=message, status_code=409)


class ForbiddenException(AppException):
    """Operación válida pero bloqueada por regla de negocio o permisos."""

    def __init__(self, message: str = "Insufficient permissions", code: str = "FORBIDDEN"):
        super().__init__(message=message, status_code=403, code=code)


class InsufficientStockException(AppException):
    """Stock insuficiente para completar la operación solicitada."""

    def __init__(self, message: str):
        super().__init__(message=message, status_code=409, code="INSUFFICIENT_STOCK")
