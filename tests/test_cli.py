"""Tests for the command-line interface."""

from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from importer.cli import (
    DEFAULT_DB_PATH,
    DEFAULT_LOG_FILE,
    EXIT_FATAL,
    EXIT_OK,
    EXIT_PARTIAL,
    build_arg_parser,
    main,
)
from importer.exceptions import StorageError
from tests.helpers import CsvWriter


def run(csv_file: Path | str, db_path: Path, log_path: Path, *extra: str) -> int:
    """Call the CLI with temporary database and log paths."""
    return main(
        [str(csv_file), "--db", str(db_path), "--log-file", str(log_path), *extra]
    )


def test_defaults() -> None:
    args = build_arg_parser().parse_args(["users.csv"])
    assert args.csv_file == "users.csv"
    assert args.db == DEFAULT_DB_PATH
    assert args.log_file == DEFAULT_LOG_FILE
    assert args.log_level == "INFO"
    assert args.verbose is False


def test_log_level_is_case_insensitive() -> None:
    args = build_arg_parser().parse_args(["x.csv", "--log-level", "debug"])
    assert args.log_level == "DEBUG"


def test_successful_import(
    valid_csv: Path,
    db_path: Path,
    log_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert run(valid_csv, db_path, log_path) == EXIT_OK

    out = capsys.readouterr()
    assert "[OK] All 3 row(s) imported successfully." in out.out
    assert out.err == ""
    assert db_path.exists()
    assert "Imported user U1" in log_path.read_text(encoding="utf-8")


def test_partial_import_returns_2(
    write_csv: CsvWriter,
    db_path: Path,
    log_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    csv_file = write_csv("user_id,name,email\nU1,Alice,a@x.com\nU2,,b@x.com\n")

    assert run(csv_file, db_path, log_path) == EXIT_PARTIAL
    assert "PROBLEMS (1)" in capsys.readouterr().out


def test_missing_file_returns_1(
    tmp_path: Path,
    db_path: Path,
    log_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert run(tmp_path / "missing.csv", db_path, log_path) == EXIT_FATAL

    out = capsys.readouterr().out
    assert "IMPORT FAILED" in out
    assert "CSV file not found" in out
    assert not db_path.exists()


def test_storage_error_returns_1(
    valid_csv: Path,
    db_path: Path,
    log_path: Path,
    mocker: MockerFixture,
    capsys: pytest.CaptureFixture[str],
) -> None:
    mocker.patch("importer.cli.ImportService.run", side_effect=StorageError("boom"))

    assert run(valid_csv, db_path, log_path) == EXIT_FATAL
    assert "Check the --db path" in capsys.readouterr().out


def test_verbose_prints_logs_to_stderr(
    valid_csv: Path,
    db_path: Path,
    log_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    run(valid_csv, db_path, log_path, "--verbose")
    assert "| INFO     | importer.service | Imported user U1" in capsys.readouterr().err


def test_help_exits_cleanly(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as caught:
        main(["--help"])

    assert caught.value.code == 0
    assert "Exit codes" in capsys.readouterr().out


def test_bad_log_level_is_rejected(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as caught:
        main(["users.csv", "--log-level", "LOUD"])

    assert caught.value.code == 2
    assert "invalid choice" in capsys.readouterr().err


def test_reads_sys_argv_when_no_args_given(
    valid_csv: Path,
    db_path: Path,
    log_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "sys.argv",
        ["importer", str(valid_csv), "--db", str(db_path), "--log-file", str(log_path)],
    )
    assert main() == EXIT_OK
