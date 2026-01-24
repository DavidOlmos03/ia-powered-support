"""
This module sets up structured, context-aware logging for the application using structlog.

Structured logging is crucial for modern applications, especially in distributed
systems, as it allows for easier parsing, filtering, and analysis of logs.
This configuration ensures that logs are emitted as JSON in production for
machine readability and as human-friendly colored text in development for
ease of debugging.

Key features:
- JSON output in production, console-friendly output in development.
- Automatic inclusion of timestamps, log levels, and logger names.
- Integration with `contextvars` to enrich logs with request-specific context.
- Automatic rendering of exception information.
"""

import logging
import sys
from typing import Any

import structlog

from app.config import settings


def configure_logging() -> None:
    """
    Configures structured logging for the entire application.

    This function should be called once at application startup.

    It sets up a chain of `structlog` processors that enrich log records
    with contextual information. The final output format is determined by the
    application's environment (`app_env` setting):
    - "production": Logs are rendered as a single JSON string per line.
    - "dev" or "staging": Logs are rendered in a colorized, human-readable format.

    The log level is determined by the `log_level` setting.
    """
    # Base configuration for Python's standard logging.
    # This is necessary because structlog builds on top of it.
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=settings.log_level.upper(),
    )

    # `structlog` processor chain. Processors are applied in order.
    structlog.configure(
        processors=[
            # Adds any context bound to `structlog.contextvars`.
            structlog.contextvars.merge_contextvars,
            # Filters messages by level, based on the standard library's configuration.
            structlog.stdlib.filter_by_level,
            # Adds the logger's name to the event dictionary.
            structlog.stdlib.add_logger_name,
            # Adds the log level to the event dictionary.
            structlog.stdlib.add_log_level,
            # Formats positional arguments from the log message.
            structlog.stdlib.PositionalArgumentsFormatter(),
            # Adds a timestamp to the log entry.
            structlog.processors.TimeStamper(fmt="iso"),
            # Renders stack traces in a structured way.
            structlog.processors.StackInfoRenderer(),
            # Adds formatted exception info to the log entry.
            structlog.processors.format_exc_info,
            # Decodes byte strings to Unicode.
            structlog.processors.UnicodeDecoder(),
            # Determines the final output format.
            structlog.processors.JSONRenderer()
            if settings.app_env == "production"
            else structlog.dev.ConsoleRenderer(colors=True),
        ],
        # `structlog` will use `logging.Logger` as its underlying logger.
        wrapper_class=structlog.stdlib.BoundLogger,
        # The context class for `bind()` and `new()`.
        context_class=dict,
        # Use the standard library's logger factory.
        logger_factory=structlog.stdlib.LoggerFactory(),
        # Cache the logger instance for performance.
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> Any:
    """
    Retrieves a `structlog` logger instance for a given module name.

    This is a convenience wrapper around `structlog.get_logger`. Using this
    function ensures that all parts of the application get a logger that is
    correctly configured with the processor chain defined in `configure_logging`.

    Args:
        name: The name for the logger, typically `__name__` of the calling module.

    Returns:
        A configured `structlog` logger instance.
    """
    return structlog.get_logger(name)
