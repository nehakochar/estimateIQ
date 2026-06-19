"""
logging_config.py

Configures structured file-based logging for the EstimateIQ backend.

Creates two log files under /app/logs/:
  - estimateiq.log      : all INFO+ messages (general activity)
  - estimateiq_errors.log : only ERROR+ messages (failures only, easy to grep)

Both files rotate at 10 MB and keep 5 backups so disk never fills up.

Usage:
    from app.core.logging_config import setup_logging
    setup_logging()   # call once at app startup

After calling setup_logging(), every logger.error() / logger.exception() call
in the codebase automatically writes to both the console AND the error log file.
"""

import logging
import logging.handlers
import os
from pathlib import Path


def setup_logging() -> None:
    log_dir = Path("/app/logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # ── Handler 1: Console (stdout — visible in `docker logs`) ──────────────
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(fmt)

    # ── Handler 2: Full log — INFO+ (all activity) ──────────────────────────
    full_log = logging.handlers.RotatingFileHandler(
        filename=log_dir / "estimateiq.log",
        maxBytes=10 * 1024 * 1024,   # 10 MB per file
        backupCount=5,                # keep estimateiq.log.1 … .5
        encoding="utf-8",
    )
    full_log.setLevel(logging.INFO)
    full_log.setFormatter(fmt)

    # ── Handler 3: Error log — ERROR+ only (failures only) ──────────────────
    error_log = logging.handlers.RotatingFileHandler(
        filename=log_dir / "estimateiq_errors.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    error_log.setLevel(logging.ERROR)
    error_log.setFormatter(fmt)

    # ── Wire into root logger ────────────────────────────────────────────────
    root = logging.getLogger()
    root.setLevel(logging.INFO)

    # Remove existing handlers to avoid duplicates when called multiple times
    root.handlers.clear()
    root.addHandler(console)
    root.addHandler(full_log)
    root.addHandler(error_log)

    # Silence noisy third-party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("google.auth").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    logging.getLogger(__name__).info(
        "Logging initialised — writing to %s", log_dir
    )
