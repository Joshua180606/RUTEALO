"""
Centralized logging configuration.

Provides:
- JSON-formatted structured logging
- File rotation with configurable size
- Separate handlers for different log levels
- Console output with color coding (development)
- Production-ready logging setup
"""

import logging
import logging.handlers
import json
import os
from pathlib import Path
from typing import Optional
from datetime import datetime


class JsonFormatter(logging.Formatter):
    """Custom formatter that outputs logs as JSON for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if provided
        if hasattr(record, 'extra'):
            log_data.update(record.extra)
        
        return json.dumps(log_data, default=str)


class ColoredFormatter(logging.Formatter):
    """Console formatter with color coding for development."""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with color coding."""
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_logging(
    log_dir: str = "logs",
    log_level: str = "INFO",
    is_production: bool = False
) -> None:
    """
    Configure centralized logging for the entire application.
    
    Args:
        log_dir: Directory to store log files (default: "logs")
        log_level: Minimum logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        is_production: If True, uses JSON formatting; if False, uses colored console output
    """
    
    # Create logs directory if it doesn't exist
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level))
    
    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()
    
    # Common formatter
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    if is_production:
        # PRODUCTION: JSON-formatted file logging only
        json_formatter = JsonFormatter()
        
        # Main log file (all levels)
        main_handler = logging.handlers.RotatingFileHandler(
            log_path / "application.log",
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5
        )
        main_handler.setLevel(logging.DEBUG)
        main_handler.setFormatter(json_formatter)
        root_logger.addHandler(main_handler)
        
        # Error log file (errors only)
        error_handler = logging.handlers.RotatingFileHandler(
            log_path / "errors.log",
            maxBytes=5 * 1024 * 1024,  # 5 MB
            backupCount=3
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(json_formatter)
        root_logger.addHandler(error_handler)
        
    else:
        # DEVELOPMENT: Colored console output
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        colored_formatter = ColoredFormatter(log_format)
        console_handler.setFormatter(colored_formatter)
        root_logger.addHandler(console_handler)
        
        # Also write to file in development for debugging
        file_handler = logging.handlers.RotatingFileHandler(
            log_path / "debug.log",
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=3
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(log_format))
        root_logger.addHandler(file_handler)
    
    # Suppress verbose third-party loggers
    logging.getLogger('pymongo').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('google.generativeai').setLevel(logging.WARNING)
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    
    root_logger.info(f"Logging initialized: level={log_level}, production={is_production}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        logging.Logger: Configured logger instance
    """
    return logging.getLogger(name)
