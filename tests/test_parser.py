"""Tests for the CSV parser."""

from collections.abc import Callable
from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from importer.exceptions import CsvFileNotFoundError, FileFormatError
from importer.parser import CsvParser, open_csv

HEADER = "user_id,name,email\n"
ALICE = {"user_id": "U1", "name": "Alice", "email": "a@x.com"}


@pytest.mark.parametrize(
    ("content", "expected"),
    [
        pytest.param(HEADER + "U1,Alice,a@x.com\n", [(2, ALICE, 3)], id="simple"),
        pytest.param(
            "\ufeff User_ID ,NAME,Email\nU1,Alice,a@x.com\n",
            [(2, ALICE, 3)],
            id="bom-and-header-case",
        ),
        pytest.param(HEADER + " U1 , Alice ,a@x.com\n", [(2, ALICE, 3)], id="trimmed"),
        pytest.param(HEADER + "\n  \nU1,Alice,a@x.com\n", [(4, ALICE, 3)], id="blanks"),
        pytest.param(
            "email,user_id,name\na@x.com,U1,Alice\n", [(2, ALICE, 3)], id="order"
        ),
        pytest.param(
            HEADER + 'U1,"Smith, Ann",a@x.com\r\n',
            [(2, {**ALICE, "name": "Smith, Ann"}, 3)],
            id="quoted-comma",
        ),
        pytest.param(
            HEADER + "U1,Alice\n", [(2, {**ALICE, "email": ""}, 2)], id="short"
        ),
        pytest.param(HEADER + "U1,Alice,a@x.com,x\n", [(2, ALICE, 4)], id="long"),
        pytest.param(HEADER, [], id="header-only"),
    ],
)
def test_parses_valid_files(
    write_csv: Callable[[str], Path],
    content: str,
    expected: list[tuple[int, dict[str, str], int]],
) -> None:
    rows = list(CsvParser().parse(write_csv(content)))
    assert [(r.line_number, r.data, r.column_count) for r in rows] == expected


@pytest.mark.parametrize(
    ("content", "message"),
    [
        (b"", "CSV file is empty"),
        (b"id,name\n1,A\n", "missing required headers: user_id, email"),
        (b"user_id,name,email\nU1,Jos\xe9,j@x.com\n", "Cannot read CSV file"),
    ],
)
def test_rejects_bad_files(tmp_path: Path, content: bytes, message: str) -> None:
    path = tmp_path / "bad.csv"
    path.write_bytes(content)
    with pytest.raises(FileFormatError, match=message):
        list(CsvParser().parse(path))


def test_missing_file(tmp_path: Path) -> None:
    with pytest.raises(CsvFileNotFoundError, match="CSV file not found"):
        list(CsvParser().parse(tmp_path / "missing.csv"))


def test_open_csv_closes_file_and_reports_permission_errors(
    write_csv: Callable[[str], Path], mocker: MockerFixture
) -> None:
    path = write_csv(HEADER)
    with open_csv(path) as handle:
        assert not handle.closed
    assert handle.closed

    mocker.patch.object(Path, "open", side_effect=PermissionError("denied"))
    with pytest.raises(FileFormatError, match="Cannot open CSV file"), open_csv(path):
        pass
