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
    "error",
    [
        CsvFileNotFoundError("users.csv"),
        FileFormatError("bad headers"),
        ValidationError(3, "email", "not valid"),
        DuplicateUserError("U1", "user_id"),
        StorageError("disk full"),
    ],
)
def test_all_errors_are_importer_errors(error: ImporterError) -> None:
    assert isinstance(error, ImporterError)
    assert isinstance(error, Exception)


def test_base_class_catches_specific_errors() -> None:
    with pytest.raises(ImporterError) as caught:
        raise StorageError("disk full")
    assert isinstance(caught.value, StorageError)
    assert str(caught.value) == "disk full"


def test_csv_file_not_found_error_keeps_path() -> None:
    error = CsvFileNotFoundError("data/missing.csv")
    assert error.path == "data/missing.csv"
    assert str(error) == "CSV file not found: data/missing.csv"


def test_validation_error_keeps_details() -> None:
    error = ValidationError(7, "email", "'bob' is not valid")
    assert (error.line_number, error.field, error.reason) == (
        7,
        "email",
        "'bob' is not valid",
    )
    assert str(error) == "Line 7: invalid 'email' ('bob' is not valid)"


@pytest.mark.parametrize("field", ["user_id", "email"])
def test_duplicate_user_error_keeps_details(field: str) -> None:
    error = DuplicateUserError("U9", field)
    assert error.user_id == "U9"
    assert error.field == field
    assert str(error) == f"Duplicate user 'U9': {field} already exists"
