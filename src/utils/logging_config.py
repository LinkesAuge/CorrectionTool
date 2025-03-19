"""
logging_config.py

Description: Configures application-wide logging with timestamps and proper formatting
Usage:
    from src.utils.logging_config import configure_logging
    configure_logging()
"""

import logging
import sys
from pathlib import Path
from datetime import datetime


def configure_logging(log_to_file=True, debug_mode=False):
    """
    Configure logging for the application with detailed timestamps.

    Args:
        log_to_file (bool): Whether to log to a file
        debug_mode (bool): Whether to set logging level to DEBUG
    """
    # Create logger
    root_logger = logging.getLogger()

    # Clear any existing handlers
    if root_logger.handlers:
        for handler in root_logger.handlers:
            root_logger.removeHandler(handler)

    # Set log level
    level = logging.DEBUG if debug_mode else logging.INFO
    root_logger.setLevel(level)

    # Create formatter with microsecond precision
    formatter = logging.Formatter(
        "%(asctime)s.%(msecs)03d - %(levelname)s - %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler (if enabled)
    if log_to_file:
        # Create logs directory if it doesn't exist
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        # Create log file with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"correction_tool_{timestamp}.log"

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

        # Also keep the default log file for backward compatibility
        default_log_file = Path("correction_tool.log")
        default_file_handler = logging.FileHandler(default_log_file, encoding="utf-8")
        default_file_handler.setFormatter(formatter)
        root_logger.addHandler(default_file_handler)

    # Log initial message
    root_logger.info(f"Logging initialized with level: {logging.getLevelName(level)}")
    if log_to_file:
        root_logger.info(f"Logging to file: {log_file}")

    # Set excepthook to log unhandled exceptions
    def exception_handler(exc_type, exc_value, exc_traceback):
        root_logger.critical("Unhandled exception", exc_info=(exc_type, exc_value, exc_traceback))
        sys.__excepthook__(exc_type, exc_value, exc_traceback)

    sys.excepthook = exception_handler
