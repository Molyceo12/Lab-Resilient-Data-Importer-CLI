"""Tests for the custom exception hierarchy."""

import pytest

from importer.exceptions import (
    CsvFileNotFoundError,
    DuplicateUserError,
    FileFormatError,
    ImporterError,
    StorageError,
    ValidationError,
)


@pytest.mark.parametrize(
    ("error", "message"),
    [
        (
            CsvFileNotFoundError("CSV file not found: x.csv"),
            "CSV file not found: x.csv",
        ),
        (FileFormatError("bad headers"), "bad headers"),
        (StorageError("disk full"), "disk full"),
        (ValidationError(7, "email", "bad"), "Line 7: invalid 'email' (bad)"),
        (
            DuplicateUserError("U9", "email"),
            "Duplicate user 'U9': email already exists",
        ),
    ],
)
def test_errors_are_importer_errors(error: ImporterError, message: str) -> None:
    assert isinstance(error, ImporterError)
    assert str(error) == message


def test_errors_keep_their_details() -> None:
    error = ValidationError(7, "email", "bad")
    duplicate = DuplicateUserError("U9", "user_id")
    assert (error.line_number, error.field, error.reason) == (7, "email", "bad")
    assert (duplicate.user_id, duplicate.field) == ("U9", "user_id")
