#!/usr/bin/env python3
"""
Simple Celery Logging Configuration
Attach to your Celery app via signals.
"""

import logging
from pathlib import Path
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler

from celery.signals import after_setup_logger, after_setup_task_logger

# -------------------------------------------------------------------
# Constants
# -------------------------------------------------------------------

LOG_ROOT = Path("logs")
MAX_MAIN_LOG_SIZE = 10 * 1024 * 1024  # 10MB
MAX_ERROR_LOG_SIZE = 5 * 1024 * 1024  # 5MB


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------

def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _current_log_dirs():
    now = datetime.now(timezone.utc)
    month_year = f"{now.strftime('%B')}-{now.year}"
    day = str(now.day)

    main_dir = LOG_ROOT / "main" / month_year
    error_dir = LOG_ROOT / "errors" / month_year

    _ensure_dir(main_dir)
    _ensure_dir(error_dir)

    return (
        main_dir / f"{day}_celery.log",
        error_dir / f"{day}_error.log",
    )


# -------------------------------------------------------------------
# Logging setup
# -------------------------------------------------------------------

def setup_celery_logging() -> None:
    """
    Configure root logging for Celery workers and tasks.
    Call once during app initialization.
    """

    main_log, error_log = _current_log_dirs()

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()

    # Main file handler
    file_handler = RotatingFileHandler(
        filename=main_log,
        maxBytes=MAX_MAIN_LOG_SIZE,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(
        logging.Formatter(
            "[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )

    # Error-only file handler
    error_handler = RotatingFileHandler(
        filename=error_log,
        maxBytes=MAX_ERROR_LOG_SIZE,
        backupCount=3,
        encoding="utf-8",
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(
        logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s]\n"
            "Message: %(message)s\n"
            "Location: %(pathname)s:%(lineno)d\n",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(
        logging.Formatter(
            "[%(asctime)s] [%(levelname)s] %(message)s",
            datefmt="%H:%M:%S",
        )
    )

    root_logger.addHandler(file_handler)
    root_logger.addHandler(error_handler)
    root_logger.addHandler(console_handler)


# -------------------------------------------------------------------
# Celery signal hooks
# -------------------------------------------------------------------

@after_setup_logger.connect
def on_after_setup_logger(logger=None, **_):
    if logger:
        logger.propagate = False


@after_setup_task_logger.connect
def on_after_setup_task_logger(logger=None, **_):
    if logger:
        logger.propagate = False
