"""End-to-end tests: real CSV files in, real JSON database out, no mocks."""

from __future__ import annotations

import json
import os
import runpy
import subprocess
import sys
from pathlib import Path

import pytest

from importer.cli import EXIT_FATAL, EXIT_OK, EXIT_PARTIAL, main

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_CSV = ROOT / "data" / "sample_users.csv"
INVALID_CSV = ROOT / "data" / "invalid_users.csv"


def run(csv_file: Path, db_path: Path, log_path: Path) -> int:
    """Run the CLI with temporary database and log paths."""
    return main([str(csv_file), "--db", str(db_path), "--log-file", str(log_path)])


def stored_ids(db_path: Path) -> list[str]:
    """Return the user ids saved in the JSON database."""
    records = json.loads(db_path.read_text(encoding="utf-8"))
    return [record["user_id"] for record in records]


def test_sample_file_imports_all_users(db_path: Path, log_path: Path) -> None:
    assert run(SAMPLE_CSV, db_path, log_path) == EXIT_OK
    assert stored_ids(db_path) == ["U001", "U002", "U003", "U004", "U005"]


def test_second_run_finds_only_duplicates(
    db_path: Path, log_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    run(SAMPLE_CSV, db_path, log_path)
    before = db_path.read_text(encoding="utf-8")
    capsys.readouterr()

    assert run(SAMPLE_CSV, db_path, log_path) == EXIT_PARTIAL

    assert "[=] Duplicate  :     5" in capsys.readouterr().out
    assert db_path.read_text(encoding="utf-8") == before


def test_invalid_file_imports_good_rows_only(
    db_path: Path, log_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert run(INVALID_CSV, db_path, log_path) == EXIT_PARTIAL

    out = capsys.readouterr().out
    assert stored_ids(db_path) == ["U101", "U106"]
    for expected in (
        "[+] Imported   :     2",
        "[-] Skipped    :     3",
        "[=] Duplicate  :     2",
        "name: value is empty",
        "email: 'irene-at-example.com' is not valid",
        "row: expected 3 columns, got 2",
        "user_id already exists (user U101)",
        "email already exists (user U105)",
    ):
        assert expected in out

    log = log_path.read_text(encoding="utf-8")
    assert "| WARNING  | importer.service | Skipped row" in log
    assert "| INFO     | importer.service | Imported user U106" in log


def test_missing_file_leaves_database_untouched(
    tmp_path: Path, db_path: Path, log_path: Path
) -> None:
    run(SAMPLE_CSV, db_path, log_path)
    before = db_path.read_bytes()

    assert run(tmp_path / "missing.csv", db_path, log_path) == EXIT_FATAL
    assert db_path.read_bytes() == before


def test_corrupt_database_is_not_overwritten(db_path: Path, log_path: Path) -> None:
    db_path.parent.mkdir(parents=True)
    db_path.write_text("{oops", encoding="utf-8")

    assert run(SAMPLE_CSV, db_path, log_path) == EXIT_FATAL
    assert db_path.read_text(encoding="utf-8") == "{oops"


# runpy warns that importer.cli is already imported by this test module; harmless.
@pytest.mark.filterwarnings("ignore::RuntimeWarning")
def test_cli_module_entry_point(
    db_path: Path, log_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "importer",
            str(SAMPLE_CSV),
            "--db",
            str(db_path),
            "--log-file",
            str(log_path),
        ],
    )

    with pytest.raises(SystemExit) as caught:
        runpy.run_module("importer.cli", run_name="__main__")

    assert caught.value.code == EXIT_OK


def test_runs_as_separate_process(tmp_path: Path) -> None:
    db_path = tmp_path / "users.json"
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "importer.cli",
            str(SAMPLE_CSV),
            "--db",
            str(db_path),
            "--log-file",
            str(tmp_path / "importer.log"),
        ],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )

    assert result.returncode == EXIT_OK, result.stderr
    assert "[OK] All 5 row(s) imported successfully." in result.stdout
    assert len(stored_ids(db_path)) == 5
