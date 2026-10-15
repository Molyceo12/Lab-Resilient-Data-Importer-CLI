"""Logging setup, called once from the CLI (never at import time)."""

from __future__ import annotations

import logging
from pathlib import Path

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
VALID_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")


def configure_logging(
    level: str = "INFO", log_file: str | Path | None = None, console: bool = True
) -> None:
    """Send log lines to ``log_file`` and, if ``console``, to the terminal.

    Raises:
        ValueError: If ``level`` is not a valid logging level name.
    """
    handlers: list[logging.Handler] = []
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))
    if console or not handlers:
        handlers.append(logging.StreamHandler())
    logging.basicConfig(
        level=level.upper(),
        format=LOG_FORMAT,
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=handlers,
        force=True,
    )
