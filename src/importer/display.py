"""Terminal output: the boxed import report and the error box (plain ASCII)."""

from __future__ import annotations

import textwrap
from pathlib import Path

from importer.exceptions import (
    CsvFileNotFoundError,
    FileFormatError,
    ImporterError,
    StorageError,
)
from importer.models import ImportSummary

WIDTH = 72
SEPARATOR = ":" * WIDTH
INNER = WIDTH - 4  # space between the "::" borders
CONTENT = INNER - 1  # one blank column before the right border
DETAILS = CONTENT - 21  # width of the DETAILS column in the problems table
TIPS = {
    CsvFileNotFoundError: "Check the CSV file path and try again.",
    FileFormatError: "Use a UTF-8 CSV file whose first row is: user_id,name,email",
    StorageError: "Check the --db path, or fix or remove the broken database file.",
}


def _wrap(text: object, width: int, indent: int) -> list[str]:
    """Wrap text to ``width``; continuation lines start with ``indent`` spaces."""
    first, *rest = textwrap.wrap(str(text), width, break_on_hyphens=False) or [""]
    return [first, *(" " * indent + part for part in rest)]


def _field(label: str, value: object) -> list[str]:
    """Return aligned ``label : value`` lines."""
    first, *rest = _wrap(value, CONTENT - 19, 19)
    return [f"  {label:<14} : {first}", *rest]


def _box(*sections: list[str]) -> str:
    """Frame sections in a ``::`` box under the title; a separator after each."""
    lines = [SEPARATOR, f"::{'RESILIENT DATA IMPORTER'.center(INNER)}::", SEPARATOR]
    for section in sections:
        lines += [f"::{text:<{INNER}}::" for text in section] + [SEPARATOR]
    return "\n".join(lines)


def _status(s: ImportSummary) -> list[str]:
    """Return the one-line verdict for an import, wrapped to fit the box."""
    bad = s.skipped + s.duplicates
    if s.total_rows == 0:
        message = "[i]  No data rows found in the file. Nothing was imported."
    elif not bad:
        message = f"[OK] All {s.imported} row(s) imported successfully."
    elif not s.imported:
        message = f"[!]  No rows imported. {bad} row(s) had problems."
    else:
        message = (
            f"[!]  Import finished: {s.imported} imported, {bad} row(s) need attention."
        )
    return [
        "  " + line
        for line in textwrap.wrap(message, CONTENT - 2, subsequent_indent=" " * 5)
    ]


def render_report(
    s: ImportSummary,
    csv_path: str | Path,
    db_path: str | Path,
    log_file: str | Path | None,
    elapsed_seconds: float,
) -> str:
    """Return the framed report shown after an import finishes."""
    files = _field("Source file", csv_path) + _field("Database", db_path)
    files += _field("Log file", log_file) if log_file is not None else []
    results = ["  IMPORT RESULTS", ""]
    for label, value in (("[+] Imported", s.imported), ("[-] Skipped", s.skipped)):
        results += _field(label, f"{value:>5}")
    results += _field("[=] Duplicate", f"{s.duplicates:>5}") + ["  " + "-" * 22]
    results += _field("    Total", f"{s.total_rows:>5}")
    status = _status(s) + [f"  Finished in {elapsed_seconds:.2f}s"]

    if not s.problems:
        return _box(files, results, status)
    problems = [f"  PROBLEMS ({len(s.problems)})", "", "  LINE  TYPE         DETAILS"]
    problems.append("  ----  ---------    " + "-" * DETAILS)
    for problem in s.problems:
        first, *rest = _wrap(problem.details, DETAILS, 21)
        problems += [f"  {problem.line_number:<6}{problem.kind:<11}  {first}", *rest]
    return _box(files, results, problems, status)


def render_error(error: ImporterError, csv_path: str | Path) -> str:
    """Return the framed message shown when an import stops with a fatal error."""
    tip = next(
        (text for kind, text in TIPS.items() if isinstance(error, kind)),
        "See the log file for details.",
    )
    details = _field("Source file", csv_path) + _field("Reason", error)
    return _box(
        ["  [X]  IMPORT FAILED - nothing was saved"], details + _field("Tip", tip)
    )
