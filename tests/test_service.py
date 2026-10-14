"""Tests for the import service, with every collaborator mocked."""

from __future__ import annotations

from collections.abc import Iterator
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from importer.exceptions import (
    CsvFileNotFoundError,
    DuplicateUserError,
    FileFormatError,
    StorageError,
    ValidationError,
)
from importer.models import RowProblem, User
from importer.parser import CsvParser, RawRow
from importer.service import ImportService
from importer.validator import UserValidator
from tests.helpers import RowFactory


@pytest.fixture
def mock_parser(mocker: MockerFixture) -> MagicMock:
    """Return a mock that behaves like a ``CsvParser``."""
    parser: MagicMock = mocker.create_autospec(CsvParser, instance=True)
    return parser


@pytest.fixture
def mock_validator(mocker: MockerFixture) -> MagicMock:
    """Return a mock that behaves like a ``UserValidator``."""
    validator: MagicMock = mocker.create_autospec(UserValidator, instance=True)
    return validator


@pytest.fixture
def service(
    mock_parser: MagicMock, mock_validator: MagicMock, mock_repository: MagicMock
) -> ImportService:
    """Return a service wired to mocks."""
    return ImportService(mock_parser, mock_validator, mock_repository)


def user(user_id: str) -> User:
    """Build a simple user for tests."""
    return User(user_id=user_id, name=f"Name {user_id}", email=f"{user_id}@x.com")


def test_imports_all_valid_rows(
    service: ImportService,
    mock_parser: MagicMock,
    mock_validator: MagicMock,
    mock_repository: MagicMock,
    make_row: RowFactory,
) -> None:
    rows = [make_row(line_number=2), make_row(line_number=3)]
    users = [user("U1"), user("U2")]
    mock_parser.parse.return_value = iter(rows)
    mock_validator.validate.side_effect = users

    summary = service.run("users.csv")

    mock_parser.parse.assert_called_once_with("users.csv")
    assert [call.args[0] for call in mock_repository.add.call_args_list] == users
    mock_repository.save.assert_called_once_with()
    assert (summary.imported, summary.skipped, summary.duplicates) == (2, 0, 0)
    assert summary.problems == []


def test_skips_bad_rows_and_keeps_going(
    service: ImportService,
    mock_parser: MagicMock,
    mock_validator: MagicMock,
    mock_repository: MagicMock,
    make_row: RowFactory,
) -> None:
    mock_parser.parse.return_value = iter(
        [make_row(line_number=n) for n in (2, 3, 4, 5)]
    )
    mock_validator.validate.side_effect = [
        user("U1"),
        ValidationError(3, "email", "'bob' is not valid"),
        user("U1"),
        user("U4"),
    ]
    mock_repository.add.side_effect = [
        None,
        DuplicateUserError("U1", "user_id"),
        None,
    ]

    summary = service.run("users.csv")

    assert (summary.imported, summary.skipped, summary.duplicates) == (2, 1, 1)
    assert summary.problems == [
        RowProblem(3, "invalid", "email: 'bob' is not valid"),
        RowProblem(4, "duplicate", "user_id already exists (user U1)"),
    ]
    assert mock_repository.add.call_count == 3
    mock_repository.save.assert_called_once_with()


def test_empty_file_still_saves(
    service: ImportService, mock_parser: MagicMock, mock_repository: MagicMock
) -> None:
    mock_parser.parse.return_value = iter([])

    summary = service.run("empty.csv")

    assert summary.total_rows == 0
    mock_repository.save.assert_called_once_with()


@pytest.mark.parametrize(
    "error",
    [CsvFileNotFoundError("missing.csv"), FileFormatError("missing headers")],
)
def test_fatal_parser_error_stops_without_saving(
    service: ImportService,
    mock_parser: MagicMock,
    mock_repository: MagicMock,
    error: Exception,
) -> None:
    mock_parser.parse.side_effect = error

    with pytest.raises(type(error)):
        service.run("users.csv")

    mock_repository.save.assert_not_called()


def test_error_midway_through_file_saves_nothing(
    service: ImportService,
    mock_parser: MagicMock,
    mock_validator: MagicMock,
    mock_repository: MagicMock,
    make_row: RowFactory,
) -> None:
    def rows_then_failure() -> Iterator[RawRow]:
        yield make_row(line_number=2)
        raise FileFormatError("Cannot read CSV file near line 3")

    mock_parser.parse.return_value = rows_then_failure()
    mock_validator.validate.return_value = user("U1")

    with pytest.raises(FileFormatError):
        service.run("users.csv")

    mock_repository.add.assert_called_once()
    mock_repository.save.assert_not_called()


def test_storage_error_on_save_is_raised(
    service: ImportService,
    mock_parser: MagicMock,
    mock_repository: MagicMock,
) -> None:
    mock_parser.parse.return_value = iter([])
    mock_repository.save.side_effect = StorageError("disk full")

    with pytest.raises(StorageError, match="disk full"):
        service.run("users.csv")
