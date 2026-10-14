"""Shared pytest fixtures."""

from __future__ import annotations

import logging
from collections.abc import Iterator
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from importer.models import User
from importer.parser import RawRow
from importer.repository import UserRepository
from tests.helpers import CsvWriter, RowFactory

VALID_CSV = (
    "user_id,name,email\n"
    "U1,Alice,alice@example.com\n"
    "U2,Bob,bob@example.com\n"
    "U3,Carol,carol@example.com\n"
)


@pytest.fixture(autouse=True)
def restore_logging() -> Iterator[None]:
    """Undo any logging setup a test makes, so tests stay independent."""
    root = logging.getLogger()
    saved_handlers = root.handlers[:]
    saved_level = root.level
    yield
    for handler in root.handlers[:]:
        if handler not in saved_handlers:
            root.removeHandler(handler)
            handler.close()
    for handler in saved_handlers:
        if handler not in root.handlers:
            root.addHandler(handler)
    root.setLevel(saved_level)


@pytest.fixture
def write_csv(tmp_path: Path) -> CsvWriter:
    """Return a function that writes CSV text to a temporary file."""

    def _write(content: str, name: str = "users.csv", encoding: str = "utf-8") -> Path:
        path = tmp_path / name
        path.write_text(content, encoding=encoding, newline="")
        return path

    return _write


@pytest.fixture
def valid_csv(write_csv: CsvWriter) -> Path:
    """Return a temporary CSV file with three valid users."""
    return write_csv(VALID_CSV)


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    """Return a path for a JSON database that does not exist yet."""
    return tmp_path / "db" / "users.json"


@pytest.fixture
def log_path(tmp_path: Path) -> Path:
    """Return a path for a temporary log file."""
    return tmp_path / "logs" / "importer.log"


@pytest.fixture
def make_row() -> RowFactory:
    """Return a function that builds a ``RawRow`` for validator tests."""

    def _make(
        user_id: str = "U1",
        name: str = "Alice",
        email: str = "alice@example.com",
        *,
        line_number: int = 2,
        column_count: int = 3,
    ) -> RawRow:
        return RawRow(
            line_number=line_number,
            data={"user_id": user_id, "name": name, "email": email},
            column_count=column_count,
            expected_columns=3,
        )

    return _make


@pytest.fixture
def sample_user() -> User:
    """Return one valid user."""
    return User(user_id="U1", name="Alice", email="alice@example.com")


@pytest.fixture
def mock_repository(mocker: MockerFixture) -> MagicMock:
    """Return a mock that behaves like a ``UserRepository``."""
    repository: MagicMock = mocker.create_autospec(UserRepository, instance=True)
    return repository
