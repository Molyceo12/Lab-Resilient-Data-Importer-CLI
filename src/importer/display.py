"""Terminal output: the import result and errors, framed in a box of colons."""

import textwrap

from importer.exceptions import ImporterError
from importer.models import ImportSummary

WIDTH = 72
BORDER = ":" * WIDTH


def box_lines(text: str) -> list[str]:
    """Return text as box lines: wrapped to fit, with '::' on both sides."""
    lines = []
    for part in textwrap.wrap(text, WIDTH - 8, subsequent_indent="    "):
        lines.append("::  " + part.ljust(WIDTH - 8) + "  ::")
    return lines


def format_report(summary: ImportSummary, csv_file: str, db_file: str) -> str:
    """Return the box shown after an import finishes."""
    if summary.has_problems:
        result = "[!] Finished, but some rows were not imported"
    else:
        result = "[OK] All rows imported successfully"

    lines = [BORDER]
    lines += box_lines("RESILIENT DATA IMPORTER")
    lines += [BORDER]
    lines += box_lines(f"File       : {csv_file}")
    lines += box_lines(f"Database   : {db_file}")
    lines += [BORDER]
    lines += box_lines(f"Imported   : {summary.imported}")
    lines += box_lines(f"Skipped    : {summary.skipped}")
    lines += box_lines(f"Duplicates : {summary.duplicates}")
    lines += [BORDER]

    if summary.problems:
        lines += box_lines(f"PROBLEMS ({len(summary.problems)})")
        for problem in summary.problems:
            text = f"Line {problem.line_number}: {problem.kind} - {problem.details}"
            lines += box_lines(text)
        lines += [BORDER]

    lines += box_lines(result)
    lines += [BORDER]
    return "\n".join(lines)


def format_error(error: ImporterError, csv_file: str) -> str:
    """Return the box shown when the import stops with an error."""
    lines = [BORDER]
    lines += box_lines("[X] IMPORT FAILED - nothing was saved")
    lines += [BORDER]
    lines += box_lines(f"File   : {csv_file}")
    lines += box_lines(f"Reason : {error}")
    lines += [BORDER]
    return "\n".join(lines)
