"""Tests for the command-line interface."""

from collections.abc import Callable
from pathlib import Path

import pytest

from importer.cli import main
from tests.helpers import VALID_CSV


@pytest.mark.parametrize(
    "case",
    [
        (VALID_CSV, 0, "[OK] All 2 row(s) imported successfully."),
        (VALID_CSV + "U3,,c@x.com\n", 2, "PROBLEMS (1)"),
        (None, 1, "CSV file not found"),  # None: the CSV file does not exist
    ],
)
def test_exit_codes(
    write_csv: Callable[[str], Path],
    db_path: Path,
    capsys: pytest.CaptureFixture[str],
    case: tuple[str | None, int, str],
) -> None:
    content, code, expected = case
    csv_file = write_csv(content) if content is not None else db_path.parent / "no.csv"
    args = [str(csv_file), "--db", str(db_path), "-v"]
    assert main([*args, "--log-file", str(db_path.parent / "importer.log")]) == code
    out = capsys.readouterr()
    assert expected in out.out
    assert "| INFO     | importer.service | Starting import" in out.err  # --verbose


@pytest.mark.parametrize(
    ("args", "code"), [(["--help"], 0), (["x.csv", "--log-level", "LOUD"], 2)]
)
def test_help_and_bad_options(args: list[str], code: int) -> None:
    with pytest.raises(SystemExit) as caught:
        main(args)
    assert caught.value.code == code
