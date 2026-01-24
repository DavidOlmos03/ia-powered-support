"""
This module defines a hierarchy of custom exception classes for the application.

Using a custom exception hierarchy allows for more granular error handling
and provides a clear, consistent structure for reporting issues across
different parts of the service. The base `AppException` captures common
attributes like a message, a machine-readable code, and an optional field
name, which can be easily serialized into a structured error response.
"""


class AppException(Exception):
    """
    Base class for all custom exceptions in this application.

    Attributes:
        message (str): A human-readable description of the error.
        code (str): A unique, machine-readable error code (e.g., "VALIDATION_ERROR").
        field (str | None): The specific input field related to the error, if applicable.
    """

    def __init__(self, message: str, code: str, field: str | None = None):
        """
        Initializes the AppException.

        Args:
            message: A human-readable description of the error.
            code: A unique, machine-readable error code.
            field: The specific input field related to the error, if applicable.
        """
        self.message = message
        self.code = code
        self.field = field
        super().__init__(message)


class ValidationError(AppException):
    """
    Raised for client-side input validation errors.

    This typically corresponds to a 400 Bad Request HTTP status code.
    It indicates that the request could not be processed because it contains
    invalid or missing data.
    """

    def __init__(self, message: str, field: str | None = None):
        super().__init__(message, "VALIDATION_ERROR", field)


class NotFoundError(AppException):
    """
    Raised when a requested resource could not be found.

    This typically corresponds to a 404 Not Found HTTP status code.
    """

    def __init__(self, message: str, field: str | None = None):
        super().__init__(message, "NOT_FOUND", field)


class BusinessLogicError(AppException):
    """
    Raised when a request violates a specific business rule.

    This typically corresponds to a 422 Unprocessable Entity HTTP status code.
    For example, trying to process a ticket that has already been completed.
    """

    def __init__(self, message: str, code: str = "BUSINESS_ERROR", field: str | None = None):
        super().__init__(message, code, field)


class ExternalServiceError(AppException):
    """
    Base class for errors related to external service failures.

    This typically corresponds to a 502 Bad Gateway or 503 Service Unavailable
    HTTP status code. It indicates a problem with a downstream dependency.
    """

    def __init__(self, message: str, code: str = "EXTERNAL_SERVICE_ERROR"):
        super().__init__(message, code)


class LLMServiceError(ExternalServiceError):
    """
    Raised for errors specifically originating from the LLM provider.
    """

    def __init__(self, message: str):
        super().__init__(message, "LLM_SERVICE_ERROR")


class LLMTimeoutError(LLMServiceError):
    """
    Raised when a request to the LLM service times out.
    """

    def __init__(self, message: str = "The request to the LLM service timed out."):
        super().__init__(message)


class LLMParseError(LLMServiceError):
    """
    Raised when the response from the LLM service is malformed or cannot be parsed.
    """

    def __init__(self, message: str = "Failed to parse the response from the LLM service."):
        super().__init__(message)


class DatabaseError(ExternalServiceError):
    """
    Raised for errors related to the database.
    """

    def __init__(self, message: str):
        super().__init__(message, "DATABASE_ERROR")


class DatabaseConnectionError(DatabaseError):
    """
    Raised specifically when the application cannot connect to the database.
    """

    def __init__(self, message: str = "Unable to establish a connection with the database."):
        super().__init__(message)
