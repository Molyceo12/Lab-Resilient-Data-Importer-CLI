"""Tests for the logging setup."""

import logging
from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from importer.logging_config import configure_logging


def handler_types() -> list[type[logging.Handler]]:
    """Return the types of the root logger's handlers."""
    return [type(handler) for handler in logging.getLogger().handlers]


@pytest.mark.parametrize("level", ["debug", "INFO", "Warning", "ERROR"])
def test_sets_level_case_insensitively(level: str) -> None:
    configure_logging(level)
    assert logging.getLogger().level == logging.getLevelName(level.upper())


def test_console_only_by_default() -> None:
    configure_logging()
    assert handler_types() == [logging.StreamHandler]


def test_invalid_level_raises() -> None:
    with pytest.raises(ValueError, match="Invalid log level: LOUD"):
        configure_logging("LOUD")


def test_writes_structured_lines_to_file(log_path: Path) -> None:
    configure_logging("INFO", log_file=log_path, console=False)
    logging.getLogger("importer.test").info("hello file")
    for handler in logging.getLogger().handlers:
        handler.flush()

    assert handler_types() == [logging.FileHandler]
    line = log_path.read_text(encoding="utf-8").strip()
    assert line.endswith("| INFO     | importer.test | hello file")


def test_file_and_console_together(log_path: Path) -> None:
    configure_logging("INFO", log_file=log_path, console=True)
    assert handler_types() == [logging.FileHandler, logging.StreamHandler]


def test_falls_back_to_console_when_file_fails(
    log_path: Path, mocker: MockerFixture, capsys: pytest.CaptureFixture[str]
) -> None:
    mocker.patch(
        "importer.logging_config.logging.FileHandler",
        side_effect=PermissionError("access denied"),
    )

    configure_logging("INFO", log_file=log_path, console=False)

    assert handler_types() == [logging.StreamHandler]
    assert "Cannot write log file" in capsys.readouterr().err


def test_replaces_previous_handlers() -> None:
    configure_logging()
    configure_logging()
    assert len(logging.getLogger().handlers) == 1
