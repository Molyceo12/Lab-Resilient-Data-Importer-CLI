"""End-to-end tests: real CSV files in, real JSON database out, no mocks."""

import json
import runpy
import sys
from pathlib import Path

import pytest

from importer.cli import main

DATA = Path(__file__).resolve().parents[1] / "data"


def run(csv_file: Path, db_path: Path) -> int:
    """Run the CLI with a temporary database and log file."""
    log = db_path.parent / "importer.log"
    return main([str(csv_file), "--db", str(db_path), "--log-file", str(log)])


def stored_ids(db_path: Path) -> list[str]:
    """Return the user ids saved in the JSON database."""
    return [r["user_id"] for r in json.loads(db_path.read_text(encoding="utf-8"))]


def test_import_then_duplicates(db_path: Path) -> None:
    assert run(DATA / "sample_users.csv", db_path) == 0
    assert stored_ids(db_path) == ["U001", "U002", "U003", "U004", "U005"]
    assert run(DATA / "sample_users.csv", db_path) == 2  # all duplicates now
    assert len(stored_ids(db_path)) == 5


def test_bad_rows_are_skipped(
    db_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert run(DATA / "invalid_users.csv", db_path) == 2
    assert stored_ids(db_path) == ["U101", "U106"]
    out = capsys.readouterr().out
    for text in ("Skipped    :     3", "Duplicate  :     2", "row: expected 3 columns"):
        assert text in out


def test_broken_database_is_not_overwritten(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True)
    db_path.write_text("{oops", encoding="utf-8")
    assert run(DATA / "sample_users.csv", db_path) == 1
    assert db_path.read_text(encoding="utf-8") == "{oops"


@pytest.mark.filterwarnings(
    "ignore::RuntimeWarning"
)  # runpy re-runs an imported module
def test_python_dash_m_entry_point(
    db_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    args = [str(DATA / "sample_users.csv"), "--db", str(db_path)]
    monkeypatch.setattr(
        sys, "argv", ["importer", *args, "--log-file", str(db_path) + ".log"]
    )
    with pytest.raises(SystemExit) as caught:
        runpy.run_module("importer.cli", run_name="__main__")
    assert caught.value.code == 0
