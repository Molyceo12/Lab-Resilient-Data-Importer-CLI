"""Tests for the logging setup."""

import logging
from pathlib import Path

import pytest

from importer.logging_config import configure_logging


def test_writes_structured_lines_to_file(tmp_path: Path) -> None:
    log_file = tmp_path / "logs" / "importer.log"
    configure_logging("debug", log_file=log_file, console=False)
    logging.getLogger("importer.test").info("hello")
    logging.shutdown()
    assert log_file.read_text(encoding="utf-8").endswith(
        "| INFO     | importer.test | hello\n"
    )
    assert logging.getLogger().level == logging.DEBUG


def test_console_only_and_bad_level() -> None:
    configure_logging()
    assert [type(h) for h in logging.getLogger().handlers] == [logging.StreamHandler]
    with pytest.raises(ValueError):
        configure_logging("LOUD")
