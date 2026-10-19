"""End-to-end tests: real CSV files in, real JSON database out, no mocks."""

import json
from pathlib import Path

from importer.cli import main

DATA = Path(__file__).resolve().parents[2] / "data"


def run(csv_file: Path, db_path: Path) -> int:
    """Run the CLI with a temporary database and log file; return the exit code."""
    log = db_path.parent / "importer.log"
    return main([str(csv_file), "--db", str(db_path), "--log-file", str(log)])


def saved_users(db_path: Path) -> list[dict[str, str]]:
    """Return the users saved in the JSON database."""
    users: list[dict[str, str]] = json.loads(db_path.read_text(encoding="utf-8"))
    return users


def test_valid_file_is_imported(db_path: Path) -> None:
    """Every user in a valid file is saved and the exit code is 0."""
    assert run(DATA / "sample_users.csv", db_path) == 0
    assert len(saved_users(db_path)) == 5


def test_bad_rows_are_skipped(db_path: Path) -> None:
    """Invalid and duplicate rows are skipped; only the 2 valid users are saved."""
    assert run(DATA / "invalid_users.csv", db_path) == 2
    assert len(saved_users(db_path)) == 2


def test_broken_database_is_not_overwritten(db_path: Path) -> None:
    """A corrupt database stops the import and is left unchanged."""
    db_path.parent.mkdir(parents=True)
    db_path.write_text("{oops", encoding="utf-8")
    assert run(DATA / "sample_users.csv", db_path) == 1
    assert db_path.read_text(encoding="utf-8") == "{oops"
