"""Tests for the import service, with the parser, validator and storage mocked."""

from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from importer.exceptions import (
    CsvFileNotFoundError,
    DuplicateUserError,
    FileFormatError,
    ValidationError,
)
from importer.models import RowProblem, User
from importer.parser import CsvParser
from importer.service import ImportService
from importer.validator import UserValidator
from tests.helpers import make_row

Mocks = tuple[MagicMock, MagicMock, MagicMock]


@pytest.fixture(name="mocks")
def fixture_mocks(mocker: MockerFixture, mock_repository: MagicMock) -> Mocks:
    """Return mock parser, validator and repository."""
    parser: MagicMock = mocker.create_autospec(CsvParser, instance=True)
    validator: MagicMock = mocker.create_autospec(UserValidator, instance=True)
    return parser, validator, mock_repository


def test_skips_bad_rows_and_keeps_going(mocks: Mocks) -> None:
    parser, validator, repository = mocks
    parser.parse.return_value = iter([make_row(line=n) for n in (2, 3, 4, 5)])
    validator.validate.side_effect = [
        User("U1", "A", "a@x.com"),
        ValidationError(3, "email", "'bob' is not valid"),
        User("U1", "A", "a@x.com"),
        User("U4", "D", "d@x.com"),
    ]
    repository.add.side_effect = [None, DuplicateUserError("U1", "user_id"), None]

    summary = ImportService(*mocks).run("users.csv")

    assert (summary.imported, summary.skipped, summary.duplicates) == (2, 1, 1)
    assert summary.problems == [
        RowProblem(3, "invalid", "email: 'bob' is not valid"),
        RowProblem(4, "duplicate", "user_id already exists (user U1)"),
    ]
    repository.save.assert_called_once_with()


@pytest.mark.parametrize("error", [CsvFileNotFoundError("x"), FileFormatError("x")])
def test_fatal_error_saves_nothing(mocks: Mocks, error: Exception) -> None:
    parser, _, repository = mocks
    parser.parse.side_effect = error
    with pytest.raises(type(error)):
        ImportService(*mocks).run("users.csv")
    repository.save.assert_not_called()
