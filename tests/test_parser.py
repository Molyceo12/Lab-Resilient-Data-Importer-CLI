"""Tests for the CSV parser."""

from __future__ import annotations

import csv
from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from importer.exceptions import CsvFileNotFoundError, FileFormatError
from importer.parser import CsvParser, RawRow, open_csv
from tests.helpers import CsvWriter

HEADER = "user_id,name,email\n"


def parse(path: Path) -> list[RawRow]:
    """Read every row of a CSV file with the default parser."""
    return list(CsvParser().parse(path))


def test_parses_valid_file(valid_csv: Path) -> None:
    rows = parse(valid_csv)

    assert [row.line_number for row in rows] == [2, 3, 4]
    assert rows[0].data == {
        "user_id": "U1",
        "name": "Alice",
        "email": "alice@example.com",
    }
    assert all(row.column_count == row.expected_columns == 3 for row in rows)


@pytest.mark.parametrize(
    ("content", "expected"),
    [
        pytest.param(
            HEADER + "U1,Alice,a@x.com\n",
            [(2, {"user_id": "U1", "name": "Alice", "email": "a@x.com"})],
            id="simple",
        ),
        pytest.param(
            " User_ID , NAME ,Email\nU1,Alice,a@x.com\n",
            [(2, {"user_id": "U1", "name": "Alice", "email": "a@x.com"})],
            id="headers-case-and-spaces",
        ),
        pytest.param(
            HEADER + "  U1 ,  Alice  , a@x.com \n",
            [(2, {"user_id": "U1", "name": "Alice", "email": "a@x.com"})],
            id="values-trimmed",
        ),
        pytest.param(
            HEADER + "U1,Alice,a@x.com\n\n   \nU2,Bob,b@x.com\n",
            [
                (2, {"user_id": "U1", "name": "Alice", "email": "a@x.com"}),
                (5, {"user_id": "U2", "name": "Bob", "email": "b@x.com"}),
            ],
            id="blank-lines-skipped",
        ),
        pytest.param(
            HEADER + 'U1,"Smith, Ann",ann@x.com\r\n',
            [(2, {"user_id": "U1", "name": "Smith, Ann", "email": "ann@x.com"})],
            id="quoted-comma-and-crlf",
        ),
        pytest.param(
            "email,user_id,name\na@x.com,U1,Alice\n",
            [(2, {"email": "a@x.com", "user_id": "U1", "name": "Alice"})],
            id="columns-in-any-order",
        ),
        pytest.param(HEADER, [], id="header-only"),
    ],
)
def test_parses_valid_inputs(
    write_csv: CsvWriter,
    content: str,
    expected: list[tuple[int, dict[str, str]]],
) -> None:
    rows = parse(write_csv(content))
    assert [(row.line_number, row.data) for row in rows] == expected


def test_reads_file_with_utf8_bom(write_csv: CsvWriter) -> None:
    path = write_csv(HEADER + "U1,Alice,a@x.com\n", encoding="utf-8-sig")
    assert parse(path)[0].data["user_id"] == "U1"


@pytest.mark.parametrize(
    ("line", "column_count", "data"),
    [
        pytest.param(
            "U1,Alice\n",
            2,
            {"user_id": "U1", "name": "Alice", "email": ""},
            id="too-few-columns",
        ),
        pytest.param(
            "U1,Alice,a@x.com,extra\n",
            4,
            {"user_id": "U1", "name": "Alice", "email": "a@x.com"},
            id="too-many-columns",
        ),
    ],
)
def test_reports_wrong_column_count(
    write_csv: CsvWriter, line: str, column_count: int, data: dict[str, str]
) -> None:
    row = parse(write_csv(HEADER + line))[0]
    assert row.column_count == column_count
    assert row.expected_columns == 3
    assert row.data == data


@pytest.mark.parametrize(
    ("content", "message"),
    [
        pytest.param("", "CSV file is empty", id="empty-file"),
        pytest.param(
            "id,name\n1,Alice\n",
            "missing required headers: user_id, email",
            id="missing-headers",
        ),
        pytest.param(
            "name,email\nAlice,a@x.com\n",
            "missing required headers: user_id",
            id="missing-one-header",
        ),
    ],
)
def test_rejects_bad_files(write_csv: CsvWriter, content: str, message: str) -> None:
    with pytest.raises(FileFormatError, match=message):
        parse(write_csv(content))


def test_missing_file_raises(tmp_path: Path) -> None:
    missing = tmp_path / "missing.csv"
    with pytest.raises(CsvFileNotFoundError) as caught:
        parse(missing)
    assert caught.value.path == str(missing)


def test_non_utf8_file_raises_without_fake_line_number(tmp_path: Path) -> None:
    path = tmp_path / "latin1.csv"
    path.write_bytes(b"user_id,name,email\nU1,Jos\xe9,jose@x.com\n")

    with pytest.raises(FileFormatError) as caught:
        parse(path)

    assert "Cannot read CSV file" in str(caught.value)
    assert "near line" not in str(caught.value)


def test_csv_error_mentions_line_number(valid_csv: Path, mocker: MockerFixture) -> None:
    class BrokenReader:
        line_num = 5

        def __init__(self) -> None:
            self._rows = iter([["user_id", "name", "email"]])

        def __iter__(self) -> BrokenReader:
            return self

        def __next__(self) -> list[str]:
            row = next(self._rows, None)
            if row is None:
                raise csv.Error("unexpected end of data")
            return row

    mocker.patch("importer.parser.csv.reader", return_value=BrokenReader())

    with pytest.raises(FileFormatError, match="near line 5: unexpected end of data"):
        parse(valid_csv)


def test_custom_required_headers(write_csv: CsvWriter) -> None:
    parser = CsvParser(required_headers=("id",))
    rows = list(parser.parse(write_csv("id,label\n1,first\n")))
    assert rows[0].data == {"id": "1", "label": "first"}


def test_open_csv_closes_file(valid_csv: Path) -> None:
    with open_csv(valid_csv) as handle:
        assert not handle.closed
    assert handle.closed


def test_open_csv_closes_file_on_error(valid_csv: Path) -> None:
    with pytest.raises(RuntimeError), open_csv(valid_csv) as handle:
        raise RuntimeError("boom")
    assert handle.closed


def test_open_csv_unreadable_file_raises(
    valid_csv: Path, mocker: MockerFixture
) -> None:
    mocker.patch.object(Path, "open", side_effect=PermissionError("access denied"))

    with (
        pytest.raises(FileFormatError, match="Cannot open CSV file"),
        open_csv(valid_csv),
    ):
        pass
