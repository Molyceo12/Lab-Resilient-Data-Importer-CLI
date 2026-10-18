"""Tests for the import service, with the parser, validator and storage mocked."""

from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from importer.exceptions import CsvFileNotFoundError
from importer.models import User
from importer.parser import CsvParser
from importer.service import ImportService
from importer.validator import UserValidator
from tests.helpers import make_row

ALICE = User("U1", "Alice", "alice@example.com")
Mocks = tuple[MagicMock, MagicMock, MagicMock]


@pytest.fixture(name="mocks")
def fixture_mocks(mocker: MockerFixture, mock_repository: MagicMock) -> Mocks:
    """Return mock parser, validator and repository."""
    parser: MagicMock = mocker.create_autospec(CsvParser, instance=True)
    validator: MagicMock = mocker.create_autospec(UserValidator, instance=True)
    return parser, validator, mock_repository


def test_valid_row_is_saved(mocks: Mocks) -> None:
    """A valid row is added to the repository and saved."""
    parser, validator, repository = mocks
    parser.parse.return_value = [make_row()]
    validator.validate.return_value = ALICE

    summary = ImportService(*mocks).run("users.csv")

    assert summary.imported == 1
    repository.add.assert_called_once_with(ALICE)
    repository.save.assert_called_once()


def test_missing_csv_saves_nothing(mocks: Mocks) -> None:
    """A missing CSV file stops the import before anything is saved."""
    parser, _, repository = mocks
    parser.parse.side_effect = CsvFileNotFoundError("x")
    with pytest.raises(CsvFileNotFoundError):
        ImportService(*mocks).run("users.csv")
    repository.save.assert_not_called()
