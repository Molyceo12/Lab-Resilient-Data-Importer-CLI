"""Tests for the terminal report."""

import pytest

from importer.display import BORDER, SEPARATOR, WIDTH, render_error, render_report
from importer.exceptions import (
    CsvFileNotFoundError,
    FileFormatError,
    ImporterError,
    StorageError,
    ValidationError,
)
from importer.models import ImportSummary, RowProblem


def assert_framed(text: str) -> None:
    """Check every line is exactly WIDTH wide and has borders on both sides."""
    for line in text.splitlines():
        assert len(line) == WIDTH, line
        assert line == SEPARATOR or (
            line.startswith(BORDER) and line.endswith(BORDER)
        ), line


def report(summary: ImportSummary, log_file: str | None = "output/importer.log") -> str:
    """Render a report with fixed paths and timing."""
    return render_report(summary, "data/users.csv", "output/users.json", log_file, 0.5)


def test_report_shows_paths_counts_and_time() -> None:
    text = report(ImportSummary(imported=5))

    assert_framed(text)
    for expected in (
        "RESILIENT DATA IMPORTER",
        "data/users.csv",
        "output/users.json",
        "output/importer.log",
        "[+] Imported   :     5",
        "Finished in 0.50s",
    ):
        assert expected in text


def test_report_without_log_file() -> None:
    assert "Log file" not in report(ImportSummary(imported=1), log_file=None)


@pytest.mark.parametrize(
    ("summary", "status"),
    [
        pytest.param(ImportSummary(), "[i]  No data rows found", id="empty"),
        pytest.param(
            ImportSummary(imported=3), "[OK] All 3 row(s) imported", id="all-good"
        ),
        pytest.param(
            ImportSummary(skipped=2, duplicates=1),
            "[!]  No rows imported. 3 row(s) had problems.",
            id="none-imported",
        ),
        pytest.param(
            ImportSummary(imported=2, skipped=1),
            "[!]  Import finished: 2 imported, 1 row(s) need attention.",
            id="mixed",
        ),
    ],
)
def test_report_status_line(summary: ImportSummary, status: str) -> None:
    text = report(summary)
    assert_framed(text)
    assert status in text


def test_report_lists_problems_in_a_table() -> None:
    summary = ImportSummary(
        imported=1,
        skipped=1,
        duplicates=1,
        problems=[
            RowProblem(3, "invalid", "name: value is empty"),
            RowProblem(4, "duplicate", "email already exists (user U2)"),
        ],
    )
    text = report(summary)

    assert_framed(text)
    assert "PROBLEMS (2)" in text
    assert "LINE  TYPE         DETAILS" in text
    assert "3     invalid      name: value is empty" in text
    assert "4     duplicate    email already exists (user U2)" in text


def test_long_values_wrap_inside_the_box() -> None:
    long_path = "C:\\very\\long\\folder\\name" * 6
    summary = ImportSummary(
        skipped=1, problems=[RowProblem(2, "invalid", "word " * 40)]
    )
    text = render_report(summary, long_path, long_path, long_path, 0.0)

    assert_framed(text)
    assert len(text.splitlines()) > 25


@pytest.mark.parametrize(
    ("error", "tip"),
    [
        pytest.param(
            CsvFileNotFoundError("x.csv"), "Check the CSV file path", id="csv"
        ),
        pytest.param(FileFormatError("bad"), "Use a UTF-8 CSV file", id="format"),
        pytest.param(StorageError("bad"), "Check the --db path", id="storage"),
        pytest.param(
            ValidationError(2, "email", "bad"), "See the log file", id="other"
        ),
    ],
)
def test_error_box_shows_reason_and_tip(error: ImporterError, tip: str) -> None:
    text = render_error(error, "data/users.csv")

    assert_framed(text)
    assert "[X]  IMPORT FAILED - nothing was saved" in text
    assert "data/users.csv" in text
    assert tip in text
