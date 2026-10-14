# Resilient Data Importer CLI

A Python command-line tool that imports user data from a CSV file into a JSON
database (a simulated database). It is built to be **resilient**: missing files,
malformed rows, invalid data and duplicate users never crash the tool or corrupt
the database. Bad rows are skipped and reported, good rows are saved.

![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen)
![Code style: black](https://img.shields.io/badge/code%20style-black-000000)

---

## Table of contents

1. [Features](#features)
2. [Requirements](#requirements)
3. [Setup](#setup)
4. [Usage](#usage)
5. [CSV format and sample data](#csv-format-and-sample-data)
6. [Project structure](#project-structure)
7. [Design](#design)
8. [Error handling](#error-handling)
9. [Logging](#logging)
10. [Testing and coverage](#testing-and-coverage)
11. [Code quality](#code-quality)
12. [Git workflow](#git-workflow)

---

## Features

- Imports users (`user_id`, `name`, `email`) from CSV into a JSON file
- **Keeps going on bad rows**: each invalid or duplicate row is skipped and listed
  with its line number and reason
- Detects **duplicates** by `user_id` or email (case-insensitive), both against
  the existing database and within the same file
- **Safe writes**: the database is replaced atomically, so a crash or failed write
  never leaves a half-written file
- Clear, boxed terminal report and meaningful **exit codes** for scripting
- Structured logging to `output/importer.log` (or the terminal with `--verbose`)
- Custom exception hierarchy, context managers, type hints (mypy strict),
  Google-style docstrings, 100% test coverage

## Requirements

- Python **3.11+**
- [Poetry](https://python-poetry.org/) 2.x
- Git

## Setup

```bash
# 1. Clone the repository
git clone https://github.com/Molyceo12/Lab-Resilient-Data-Importer-CLI.git
cd Lab-Resilient-Data-Importer-CLI

# 2. Install Poetry (skip if already installed)
python -m pip install poetry

# 3. Install dependencies (Poetry creates the virtual environment in .venv/)
python -m poetry install

# 4. Install the pre-commit hooks (Black, ruff, mypy run before every commit)
python -m poetry run python -m pre_commit install
```

> **Why `python -m ...`?** It runs each tool through Python, so the commands work
> even when `poetry`, `pytest` or `pre-commit` are not on your PATH or their
> `.exe` launchers are blocked (for example by Windows Device Guard). If `poetry`
> works directly on your machine, `poetry install` and `poetry run ...` do the same.
>
> If mypy's compiled build is blocked on Windows, install its pure-Python build:
> `python -m poetry run python -m pip install --force-reinstall --no-deps --no-binary mypy "mypy==2.4.0"`

Without Poetry, use pip:

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (Linux/macOS: source .venv/bin/activate)
python -m pip install -r requirements.txt
python -m pip install -e .
python -m importer data/sample_users.csv
```

## Usage

```bash
python -m poetry run python -m importer <csv_file> [--db PATH] [--log-level LEVEL] [--log-file PATH] [-v]
```

| Option | Default | Description |
|---|---|---|
| `csv_file` | (required) | CSV file to import |
| `--db` | `output/users.json` | JSON database file (created if missing) |
| `--log-level` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| `--log-file` | `output/importer.log` | File that receives the detailed log |
| `-v`, `--verbose` | off | Also print log lines in the terminal |
| `-h`, `--help` | | Show help |

The `importer` console script is also installed, so `poetry run importer data/sample_users.csv` works where `.exe` launchers are allowed.

### Exit codes

| Code | Meaning |
|---|---|
| `0` | Every row was imported |
| `1` | Fatal error: missing file, bad headers, unreadable file or broken database. Nothing was saved |
| `2` | Import finished, but some rows were skipped or duplicated (also used by argparse for invalid arguments) |

### Examples

```bash
# Successful import
python -m poetry run python -m importer data/sample_users.csv

# Rows with errors and duplicates
python -m poetry run python -m importer data/invalid_users.csv

# Custom database, debug logs shown in the terminal
python -m poetry run python -m importer data/sample_users.csv --db output/test.json --log-level DEBUG -v

# Start again with an empty database
rm output/users.json            # PowerShell: Remove-Item output\users.json
```

### Sample output

```
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
::                      RESILIENT DATA IMPORTER                       ::
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
::  Source file    : data/invalid_users.csv                           ::
::  Database       : output/users.json                                ::
::  Log file       : output/importer.log                              ::
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
::  IMPORT RESULTS                                                    ::
::                                                                    ::
::  [+] Imported   :     2                                            ::
::  [-] Skipped    :     3                                            ::
::  [=] Duplicate  :     2                                            ::
::  ----------------------                                            ::
::      Total      :     7                                            ::
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
::  PROBLEMS (5)                                                      ::
::                                                                    ::
::  LINE  TYPE         DETAILS                                        ::
::  ----  ---------    ---------------------------------------------- ::
::  3     invalid      name: value is empty                           ::
::  4     invalid      email: 'irene-at-example.com' is not valid     ::
::  5     invalid      row: expected 3 columns, got 2                 ::
::  6     duplicate    user_id already exists (user U101)             ::
::  7     duplicate    email already exists (user U105)               ::
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
::  [!]  Import finished: 2 imported, 5 row(s) need attention.        ::
::  Finished in 0.00s                                                 ::
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
```

A fatal error shows what went wrong and how to fix it:

```
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
::                      RESILIENT DATA IMPORTER                       ::
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
::  [X]  IMPORT FAILED - nothing was saved                            ::
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
::  Source file    : missing.csv                                      ::
::  Reason         : CSV file not found: missing.csv                  ::
::  Tip            : Check the CSV file path and try again.           ::
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
```

## CSV format and sample data

The first row must contain the headers `user_id`, `name` and `email`
(any order, any letter case; extra columns are ignored). Files are read as UTF-8
(a UTF-8 BOM from Excel is fine), and blank lines are skipped.

```csv
user_id,name,email
U001,Alice Mukamana,alice@example.com
U002,Brian Okello,brian@example.com
```

Validation rules for each row:

- the row has as many values as there are headers
- `user_id`, `name` and `email` are not empty
- `name` is at most 100 characters
- `email` looks like `name@domain.tld` (stored in lowercase)
- `user_id` and `email` are not already in the database

| File | Purpose |
|---|---|
| `data/sample_users.csv` | 5 valid users (success demo) |
| `data/invalid_users.csv` | one row for each error type (error demo) |

The database is a JSON list of users:

```json
[
  {"user_id": "U001", "name": "Alice Mukamana", "email": "alice@example.com"}
]
```

## Project structure

```
.
├── src/importer/
│   ├── __init__.py          # package docstring and version
│   ├── __main__.py          # enables `python -m importer`
│   ├── cli.py               # argument parsing, wiring, exit codes
│   ├── display.py           # boxed terminal report and error box
│   ├── service.py           # ImportService: parse -> validate -> store
│   ├── parser.py            # CsvParser + open_csv context manager
│   ├── validator.py         # UserValidator: turns raw rows into Users
│   ├── repository.py        # UserRepository interface + JsonUserRepository
│   ├── exceptions.py        # custom exception hierarchy
│   ├── logging_config.py    # logging setup (file and/or console)
│   └── models/
│       ├── user.py          # User dataclass
│       └── summary.py       # ImportSummary and RowProblem dataclasses
├── tests/                   # unit and integration tests (pytest)
├── data/                    # sample CSV files
├── reports/coverage.txt     # test coverage report
├── .pre-commit-config.yaml  # Black, ruff, mypy and file checks
├── pyproject.toml           # Poetry project + tool configuration
├── poetry.lock
└── requirements.txt         # exported from Poetry
```

## Design

Each part has one job (Single Responsibility), and the service receives its
parts from outside (Dependency Injection), so each part can be swapped or
mocked in tests.

```
 cli.py ──> ImportService.run(csv)
               │
               ├── CsvParser.parse()        reads raw rows (RawRow)
               ├── UserValidator.validate() RawRow -> User, or ValidationError
               └── UserRepository.add()     stores User, or DuplicateUserError
                   UserRepository.save()    writes once at the end
            <── ImportSummary ──> display.render_report()
```

- **Repository pattern:** `UserRepository` is an abstract interface;
  `JsonUserRepository` is the JSON implementation. The service depends only on
  the interface (Dependency Inversion).
- **Dataclasses:** `User` (frozen), `RawRow`, `ImportSummary`, `RowProblem`.
- **Context managers:** `open_csv()` always closes the CSV file;
  `atomic_write()` writes to a temporary file and replaces the database only when
  writing succeeds.
- **One read, one write:** users are loaded once and saved once per import.

## Error handling

All expected errors inherit from `ImporterError`, so callers can catch everything
with one `except` or handle specific cases.

```
ImporterError
├── CsvFileNotFoundError   CSV path does not exist                 -> fatal (exit 1)
├── FileFormatError        empty file, missing headers, not UTF-8  -> fatal (exit 1)
├── StorageError           database unreadable, corrupt or unwritable -> fatal (exit 1)
├── ValidationError        bad row (line number, field, reason)    -> row skipped
└── DuplicateUserError     user_id or email already stored         -> row skipped
```

- Built-in errors (`FileNotFoundError`, `OSError`, `UnicodeDecodeError`,
  `csv.Error`, `json.JSONDecodeError`) are converted with `raise ... from exc`,
  so the original cause is kept.
- `try/except/else/finally` is used in the parser (read rows, `else` logs
  success, `finally` logs the end) and the service (per-row `except` for skipped
  rows, `else` for success, `finally` for the summary log).
- On a fatal error **nothing is saved**, and an existing database is never
  overwritten with partial data.

## Logging

Every module logs with `logging.getLogger(__name__)`; `logging_config.py`
configures handlers once, from the CLI.

```
2026-10-14 16:49:35 | INFO     | importer.service | Imported user U101
2026-10-14 16:49:35 | WARNING  | importer.service | Skipped row: Line 3: invalid 'name' (value is empty)
2026-10-14 16:49:35 | INFO     | importer.repository | Saved 2 users to output\users.json
```

| Level | Used for |
|---|---|
| `INFO` | start, each imported user, save, summary |
| `WARNING` | skipped and duplicate rows |
| `ERROR` | fatal errors |
| `DEBUG` | file open/close and other details |

Logs go to `output/importer.log` by default; `--verbose` also prints them to the
terminal (stderr). If the log file cannot be opened, logging falls back to the
terminal.

## Testing and coverage

```bash
# Run all tests
python -m poetry run python -m pytest

# Run with coverage (fails if coverage drops below 90%)
python -m poetry run python -m pytest --cov --cov-report=term-missing

# Optional HTML report in htmlcov/
python -m poetry run python -m pytest --cov --cov-report=html
```

**127 tests, 100% line and branch coverage** (see
[`reports/coverage.txt`](reports/coverage.txt)).

| Test file | Covers | Techniques |
|---|---|---|
| `test_exceptions.py` | hierarchy and messages | parametrize |
| `test_models.py` | User, ImportSummary | parametrize |
| `test_parser.py` | valid/invalid CSV inputs, encodings, context manager | parametrize, `tmp_path`, mocker |
| `test_validator.py` | valid and invalid rows | parametrize |
| `test_repository.py` | storage, duplicates, corrupt DB, atomic writes | `tmp_path`, mocker |
| `test_service.py` | orchestration with all parts mocked | pytest-mock (`create_autospec`) |
| `test_display.py` | report layout, statuses, error box | parametrize |
| `test_logging_config.py` | handlers, levels, file fallback | mocker, capsys |
| `test_cli.py` | arguments, exit codes, output | capsys, monkeypatch, mocker |
| `test_integration.py` | real files end to end, `python -m importer` | no mocks, subprocess |

Shared fixtures in `tests/conftest.py` provide temporary CSV files, a temporary
database path, a row factory and a mock repository.

## Code quality

| Tool | Purpose |
|---|---|
| **Black** | formatting (PEP 8, line length 88) |
| **ruff** | linting: errors, imports, naming, bug patterns, simplifications |
| **mypy** | static type checking in **strict** mode for `src/` and `tests/` |
| **pre-commit** | runs the tools above plus file checks before every commit |

```bash
python -m poetry run python -m pre_commit run --all-files
```

All modules and public functions have Google-style docstrings.

## Git workflow

The project follows **Git Flow**:

- `main`: released, stable code (tagged `v1.0.0`)
- `develop`: integration branch; features are merged here through pull requests
- `feature/*`: one branch per piece of work, created from `develop`
- `release/*`: final checks before merging `develop` into `main`

| PR | Branch | Content |
|---|---|---|
| #1 | `feature/project-setup` | Poetry, tooling, pre-commit hooks |
| #2 | `feature/core-importer` | exceptions, models, parser, validator, repository, logging |
| #3 | `feature/cli` | import service, CLI, exit codes, sample data |
| #4 | `feature/cli-output` | boxed report, file logging |
| #5 | `feature/tests-and-docs` | test suite, coverage report, README |

Commit messages follow
[Conventional Commits](https://www.conventionalcommits.org/)
(`feat:`, `fix:`, `test:`, `docs:`, `chore:`, `refactor:`).
