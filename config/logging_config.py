"""Logging configuration with structured logging support."""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from config.settings import settings

# Create logs directory if it doesn't exist
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        from datetime import timezone
        log_data: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, "agent_name"):
            log_data["agent_name"] = record.agent_name
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "execution_time"):
            log_data["execution_time"] = record.execution_time

        return json.dumps(log_data)


class TextFormatter(logging.Formatter):
    """Human-readable text formatter."""

    def __init__(self):
        """Initialize formatter."""
        super().__init__(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )


def setup_logging() -> None:
    """Configure logging for the application."""
    # Get log level from settings
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    # Choose formatter based on settings
    if settings.LOG_FORMAT == "json":
        formatter = JSONFormatter()
    else:
        formatter = TextFormatter()

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler
    log_file = LOG_DIR / f"portfolio_sentiment_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    logging.info("Logging configured successfully")


def get_agent_logger(agent_name: str) -> logging.Logger:
    """Get a logger with agent context.

    Args:
        agent_name: Name of the agent.

    Returns:
        Logger instance with agent context.
    """
    logger = logging.getLogger(f"agents.{agent_name}")

    # Add agent name to all log records
    old_factory = logging.getLogRecordFactory()

    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        record.agent_name = agent_name
        return record

    logging.setLogRecordFactory(record_factory)
    return logger


# Initialize logging on import
setup_logging()

