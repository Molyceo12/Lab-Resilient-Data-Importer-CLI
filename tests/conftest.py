"""Shared pytest fixtures: temporary CSV files, database path and mock storage."""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterator
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from importer.repository import UserRepository


@pytest.fixture(autouse=True)
def restore_logging() -> Iterator[None]:
    """Undo any logging setup a test makes, so tests stay independent."""
    root = logging.getLogger()
    saved_handlers, saved_level = root.handlers[:], root.level
    yield
    for handler in root.handlers[:]:
        root.removeHandler(handler)
        if handler not in saved_handlers:
            handler.close()
    for handler in saved_handlers:
        root.addHandler(handler)
    root.setLevel(saved_level)


@pytest.fixture(name="write_csv")
def fixture_write_csv(tmp_path: Path) -> Callable[[str], Path]:
    """Return a function that writes CSV text to a temporary file."""

    def write(content: str) -> Path:
        path = tmp_path / "users.csv"
        path.write_text(content, encoding="utf-8", newline="")
        return path

    return write


@pytest.fixture(name="db_path")
def fixture_db_path(tmp_path: Path) -> Path:
    """Return a path for a JSON database that does not exist yet."""
    return tmp_path / "db" / "users.json"


@pytest.fixture(name="mock_repository")
def fixture_mock_repository(mocker: MockerFixture) -> MagicMock:
    """Return a mock that behaves like a ``UserRepository``."""
    repository: MagicMock = mocker.create_autospec(UserRepository, instance=True)
    return repository
