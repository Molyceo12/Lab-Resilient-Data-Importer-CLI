"""Tests for the CSV parser."""

from collections.abc import Callable
from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from importer.exceptions import CsvFileNotFoundError, FileFormatError
from importer.parser import CsvParser

HEADER = "user_id,name,email\n"
ALICE = {"user_id": "U1", "name": "Alice", "email": "a@x.com"}


@pytest.mark.parametrize(
    "content",
    [
        HEADER + "U1,Alice,a@x.com\n",
        HEADER + " U1 , Alice , a@x.com \n",  # spaces are trimmed
    ],
)
def test_reads_valid_rows(write_csv: Callable[[str], Path], content: str) -> None:
    """A valid CSV file is read into one row for Alice."""
    rows = list(CsvParser().parse(write_csv(content)))
    assert rows[0].data == ALICE


@pytest.mark.parametrize(
    ("content", "message"),
    [
        ("", "CSV file is empty"),
        ("id,name\n1,A\n", "missing required headers"),
    ],
)
def test_rejects_bad_files(
    write_csv: Callable[[str], Path], content: str, message: str
) -> None:
    """An empty file or a file without the required headers is rejected."""
    with pytest.raises(FileFormatError, match=message):
        list(CsvParser().parse(write_csv(content)))


def test_missing_file(tmp_path: Path) -> None:
    """A CSV file that does not exist raises CsvFileNotFoundError."""
    with pytest.raises(CsvFileNotFoundError):
        list(CsvParser().parse(tmp_path / "missing.csv"))


def test_file_system_error(mocker: MockerFixture) -> None:
    """If the file system refuses access, FileFormatError is raised."""
    mocker.patch.object(Path, "open", side_effect=PermissionError("denied"))
    with pytest.raises(FileFormatError, match="Cannot open CSV file"):
        list(CsvParser().parse("users.csv"))
