"""
FastAPI application entry point.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.routes import api_router
from app.config import settings
from app.core.exceptions import (
    AppException,
    DatabaseError,
    LLMServiceError,
    NotFoundError,
    ValidationError,
)
from app.core.logging_config import configure_logging, get_logger

# Configure logging on module import
configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup
    logger.info(
        "Starting application",
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.app_env,
    )

    yield

    # Shutdown
    logger.info("Shutting down application")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-powered support ticket classification API",
    lifespan=lifespan,
    docs_url="/docs" if settings.app_env != "production" else None,
    redoc_url="/redoc" if settings.app_env != "production" else None,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# Request ID middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add request ID to all requests for tracking."""
    import uuid

    request_id = f"req_{uuid.uuid4().hex[:12]}"
    request.state.request_id = request_id

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id

    return response


# Exception handlers


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors."""
    errors = exc.errors()
    first_error = errors[0] if errors else {}

    field = ".".join(str(loc) for loc in first_error.get("loc", []))
    message = first_error.get("msg", "Validation error")

    logger.warning(
        "Validation error",
        request_id=getattr(request.state, "request_id", "unknown"),
        errors=errors,
    )

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": message,
                "field": field,
            },
            "request_id": getattr(request.state, "request_id", "unknown"),
        },
    )


@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError):
    """Handle custom validation errors."""
    logger.warning(
        "Custom validation error",
        request_id=getattr(request.state, "request_id", "unknown"),
        error=exc.message,
    )

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "success": False,
            "error": {
                "code": exc.code,
                "message": exc.message,
                "field": exc.field,
            },
            "request_id": getattr(request.state, "request_id", "unknown"),
        },
    )


@app.exception_handler(NotFoundError)
async def not_found_error_handler(request: Request, exc: NotFoundError):
    """Handle not found errors."""
    logger.warning(
        "Resource not found",
        request_id=getattr(request.state, "request_id", "unknown"),
        error=exc.message,
    )

    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "success": False,
            "error": {
                "code": exc.code,
                "message": exc.message,
                "field": exc.field,
            },
            "request_id": getattr(request.state, "request_id", "unknown"),
        },
    )


@app.exception_handler(LLMServiceError)
async def llm_error_handler(request: Request, exc: LLMServiceError):
    """Handle LLM service errors."""
    logger.error(
        "LLM service error",
        request_id=getattr(request.state, "request_id", "unknown"),
        error=exc.message,
        exc_info=True,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": exc.code,
                "message": "Failed to process ticket. Please try again.",
                "field": None,
            },
            "request_id": getattr(request.state, "request_id", "unknown"),
        },
    )


@app.exception_handler(DatabaseError)
async def database_error_handler(request: Request, exc: DatabaseError):
    """Handle database errors."""
    logger.error(
        "Database error",
        request_id=getattr(request.state, "request_id", "unknown"),
        error=exc.message,
        exc_info=True,
    )

    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "success": False,
            "error": {
                "code": exc.code,
                "message": "Database service unavailable. Please try again later.",
                "field": None,
            },
            "request_id": getattr(request.state, "request_id", "unknown"),
        },
    )


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """Handle generic application exceptions."""
    logger.error(
        "Application error",
        request_id=getattr(request.state, "request_id", "unknown"),
        error=exc.message,
        code=exc.code,
        exc_info=True,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": exc.code,
                "message": exc.message,
                "field": exc.field,
            },
            "request_id": getattr(request.state, "request_id", "unknown"),
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle any unhandled exceptions."""
    logger.error(
        "Unhandled exception",
        request_id=getattr(request.state, "request_id", "unknown"),
        error=str(exc),
        exc_info=True,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred. Please try again.",
                "field": None,
            },
            "request_id": getattr(request.state, "request_id", "unknown"),
        },
    )


# Include API routes
app.include_router(api_router)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.app_env,
        "docs_url": "/docs" if settings.app_env != "production" else "disabled",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.api_port,
        reload=settings.app_env == "dev",
        log_level=settings.log_level.lower(),
    )
