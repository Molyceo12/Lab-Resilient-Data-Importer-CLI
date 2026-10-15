"""Tests for the terminal report."""

import pytest

from importer.display import WIDTH, render_error, render_report
from importer.exceptions import (
    CsvFileNotFoundError,
    FileFormatError,
    ImporterError,
    StorageError,
    ValidationError,
)
from importer.models import ImportSummary, RowProblem


def assert_framed(text: str) -> None:
    """Every line is exactly WIDTH wide with ``::`` on both sides."""
    assert all(
        len(line) == WIDTH and line[:2] == line[-2:] == "::"
        for line in text.splitlines()
    )


@pytest.mark.parametrize(
    ("summary", "expected"),
    [
        (ImportSummary(), "[i]  No data rows found"),
        (ImportSummary(imported=3), "[OK] All 3 row(s) imported successfully."),
        (
            ImportSummary(skipped=2, duplicates=1),
            "[!]  No rows imported. 3 row(s) had problems.",
        ),
        (
            ImportSummary(1, 1, problems=[RowProblem(3, "invalid", "word " * 30)]),
            "3     invalid      word word",
        ),
    ],
)
def test_report(summary: ImportSummary, expected: str) -> None:
    text = render_report(
        summary, "data/users.csv", "x/" * 40, "output/importer.log", 0.5
    )
    assert_framed(text)
    assert expected in text
    assert "Finished in 0.50s" in text


def test_report_without_log_file() -> None:
    assert "Log file" not in render_report(ImportSummary(), "a.csv", "db.json", None, 0)


@pytest.mark.parametrize(
    ("error", "tip"),
    [
        (CsvFileNotFoundError("x"), "Check the CSV file path"),
        (FileFormatError("x"), "Use a UTF-8 CSV file"),
        (StorageError("x"), "Check the --db path"),
        (ValidationError(2, "email", "x"), "See the log file"),
    ],
)
def test_error_box(error: ImporterError, tip: str) -> None:
    text = render_error(error, "data/users.csv")
    assert_framed(text)
    assert "[X]  IMPORT FAILED - nothing was saved" in text
    assert tip in text
