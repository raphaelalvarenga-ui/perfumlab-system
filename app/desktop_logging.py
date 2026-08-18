from __future__ import annotations

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path


LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"


def configure_desktop_logging() -> Path:
    log_dir = _desktop_log_dir()
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "perfumlab-desktop.log"

    logger = logging.getLogger("app")
    if not _has_handler(logger, log_path):
        handler = RotatingFileHandler(
            log_path,
            maxBytes=512_000,
            backupCount=3,
            encoding="utf-8",
        )
        handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(handler)

    logger.setLevel(logging.INFO)
    return log_path


def _desktop_log_dir() -> Path:
    base = os.getenv("LOCALAPPDATA")
    if base:
        return Path(base) / "PerfumLab" / "logs"
    return Path.home() / "AppData" / "Local" / "PerfumLab" / "logs"


def _has_handler(logger: logging.Logger, log_path: Path) -> bool:
    expected = str(log_path.resolve())
    for handler in logger.handlers:
        if isinstance(handler, RotatingFileHandler):
            try:
                if str(Path(handler.baseFilename).resolve()) == expected:
                    return True
            except OSError:
                continue
    return False
