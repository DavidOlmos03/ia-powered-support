"""
Custom exception classes.
"""


class AppException(Exception):
    """Base application exception."""

    def __init__(self, message: str, code: str, field: str | None = None):
        self.message = message
        self.code = code
        self.field = field
        super().__init__(message)


class ValidationError(AppException):
    """Client-side validation error (400)."""

    def __init__(self, message: str, field: str | None = None):
        super().__init__(message, "VALIDATION_ERROR", field)


class NotFoundError(AppException):
    """Resource not found (404)."""

    def __init__(self, message: str, field: str | None = None):
        super().__init__(message, "NOT_FOUND", field)


class BusinessLogicError(AppException):
    """Business rule violation (422)."""

    def __init__(self, message: str, code: str = "BUSINESS_ERROR", field: str | None = None):
        super().__init__(message, code, field)


class ExternalServiceError(AppException):
    """External service failure (502/503)."""

    def __init__(self, message: str, code: str = "EXTERNAL_SERVICE_ERROR"):
        super().__init__(message, code)


class LLMServiceError(ExternalServiceError):
    """LLM-specific errors."""

    def __init__(self, message: str):
        super().__init__(message, "LLM_SERVICE_ERROR")


class LLMTimeoutError(LLMServiceError):
    """LLM request timeout."""

    def __init__(self, message: str = "LLM request timed out"):
        super().__init__(message)


class LLMParseError(LLMServiceError):
    """LLM response parsing error."""

    def __init__(self, message: str = "Failed to parse LLM response"):
        super().__init__(message)


class DatabaseError(ExternalServiceError):
    """Database-specific errors."""

    def __init__(self, message: str):
        super().__init__(message, "DATABASE_ERROR")


class DatabaseConnectionError(DatabaseError):
    """Database connection error."""

    def __init__(self, message: str = "Unable to connect to database"):
        super().__init__(message)
