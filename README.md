# Resilient Data Importer CLI

A Python command-line tool that imports user data from a CSV file into a JSON
database (a simulated database). It is built to be **resilient**: missing files,
malformed rows, invalid data and duplicate users never crash the tool or corrupt
the database. Bad rows are skipped and reported, good rows are saved.

![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![Coverage](https://img.shields.io/badge/coverage-96%25-brightgreen)
![Code style: black](https://img.shields.io/badge/code%20style-black-000000)

---

## Table of contents

1. [Features](#features)
2. [Requirements](#requirements)
3. [Setup](#setup)
4. [Quick commands](#quick-commands)
5. [Usage](#usage)
6. [Scenarios](#scenarios)
7. [CSV format and sample data](#csv-format-and-sample-data)
8. [Project structure](#project-structure)
9. [Design](#design)
10. [Error handling](#error-handling)
11. [Logging](#logging)
12. [Testing and coverage](#testing-and-coverage)
13. [Code quality](#code-quality)
14. [Git workflow](#git-workflow)

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
  Google-style docstrings, 96% test coverage

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
python -m importer.cli data/sample_users.csv
```

## Quick commands

Every command in one place (PowerShell). Run them from the project folder; see [Scenarios](#scenarios) for what each import prints.

**Go to the project folder**

```bash
cd Lab-Resilient-Data-Importer-CLI
```

**Import a valid file**

```bash
python -m poetry run python -m importer.cli data/sample_users.csv
```

**Import a file with bad rows**

```bash
python -m poetry run python -m importer.cli data/invalid_users.csv
```

**Import a missing file**

```bash
python -m poetry run python -m importer.cli missing.csv
```

**Import and show logs in the terminal**

```bash
python -m poetry run python -m importer.cli data/sample_users.csv -v
```

**Use another database file**

```bash
python -m poetry run python -m importer.cli data/sample_users.csv --db output/test.json
```

**Show the CLI help**

```bash
python -m poetry run python -m importer.cli --help
```

**Show the last log lines**

```bash
Get-Content output\importer.log -Tail 10
```

**Start again with an empty database**

```bash
Remove-Item output\users.json
```

**Run all tests**

```bash
python -m poetry run python -m pytest
```

**Run all tests and list their names**

```bash
python -m poetry run python -m pytest -v
```

**Run one test file**

```bash
python -m poetry run python -m pytest tests/test_parser.py -v
```

**Run tests with coverage**

```bash
python -m poetry run python -m pytest --cov --cov-report=term-missing
```

**Run the code checks (Black, ruff, mypy)**

```bash
python -m poetry run python -m pre_commit run --all-files
```

## Usage

```bash
python -m poetry run python -m importer.cli <csv_file> [--db PATH] [--log-file PATH] [-v]
```

| Option | Default | Description |
|---|---|---|
| `csv_file` | (required) | CSV file to import |
| `--db` | `output/users.json` | JSON database file (created if missing) |
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

## Scenarios

Run these from the project folder, in order. The commands are for PowerShell.

### 1. Successful import

Start with an empty database, then import a valid file. Exit code `0`.

```bash
Remove-Item output\users.json -ErrorAction SilentlyContinue
```
```bash
python -m poetry run python -m importer.cli data/sample_users.csv
```

```
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
::  RESILIENT DATA IMPORTER                                           ::
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
::  File       : data/sample_users.csv                                ::
::  Database   : output/users.json                                    ::
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
::  Imported   : 5                                                    ::
::  Skipped    : 0                                                    ::
::  Duplicates : 0                                                    ::
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
::  [OK] All rows imported successfully                               ::
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
```

### 2. Same file again (duplicates)

Every user already exists, so nothing new is saved. Exit code `2`.

```bash
python -m poetry run python -m importer.cli data/sample_users.csv
```

```
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
::  RESILIENT DATA IMPORTER                                           ::
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
::  File       : data/sample_users.csv                                ::
::  Database   : output/users.json                                    ::
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
::  Imported   : 0                                                    ::
::  Skipped    : 0                                                    ::
::  Duplicates : 5                                                    ::
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
::  PROBLEMS (5)                                                      ::
::  Line 2: duplicate - user_id already exists (user U001)            ::
::  Line 3: duplicate - user_id already exists (user U002)            ::
::  Line 4: duplicate - user_id already exists (user U003)            ::
::  Line 5: duplicate - user_id already exists (user U004)            ::
::  Line 6: duplicate - user_id already exists (user U005)            ::
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
::  [!] Finished, but some rows were not imported                     ::
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
```

### 3. Rows with errors

Good rows are saved; bad and duplicate rows are skipped and listed. Exit code `2`.

```bash
python -m poetry run python -m importer.cli data/invalid_users.csv
```

```
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
::  RESILIENT DATA IMPORTER                                           ::
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
::  File       : data/invalid_users.csv                               ::
::  Database   : output/users.json                                    ::
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
::  Imported   : 2                                                    ::
::  Skipped    : 3                                                    ::
::  Duplicates : 2                                                    ::
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
::  PROBLEMS (5)                                                      ::
::  Line 3: invalid - name: value is empty                            ::
::  Line 4: invalid - email: 'irene-at-example.com' is not valid      ::
::  Line 5: invalid - row: expected 3 columns, got 2                  ::
::  Line 6: duplicate - user_id already exists (user U101)            ::
::  Line 7: duplicate - email already exists (user U105)              ::
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
::  [!] Finished, but some rows were not imported                     ::
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
```

### 4. Missing CSV file

The import stops and nothing is saved. Exit code `1`.

```bash
python -m poetry run python -m importer.cli missing.csv
```

```
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
::  [X] IMPORT FAILED - nothing was saved                             ::
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
::  File   : missing.csv                                              ::
::  Reason : CSV file not found: missing.csv                          ::
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
```

### 5. Wrong headers

Create a file without the required headers, then import it. Exit code `1`.

```bash
Set-Content output\bad_headers.csv "id,name`n1,Ana"
```
```bash
python -m poetry run python -m importer.cli output/bad_headers.csv
```

```
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
::  [X] IMPORT FAILED - nothing was saved                             ::
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
::  File   : output/bad_headers.csv                                   ::
::  Reason : CSV file is missing required headers: user_id            ::
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
```

### 6. Empty file

Create an empty file, then import it. Exit code `1`.

```bash
New-Item output\empty.csv -ItemType File -Force
```
```bash
python -m poetry run python -m importer.cli output/empty.csv
```

```
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
::  [X] IMPORT FAILED - nothing was saved                             ::
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
::  File   : output/empty.csv                                         ::
::  Reason : CSV file is empty: output\empty.csv                      ::
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
```

### 7. Broken database

Corrupt the database, then import. The import stops and the broken file is not overwritten. Exit code `1`.

```bash
Set-Content output\users.json "{oops"
```
```bash
python -m poetry run python -m importer.cli data/sample_users.csv
```

```
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
::  [X] IMPORT FAILED - nothing was saved                             ::
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
::  File   : data/sample_users.csv                                    ::
::  Reason : Database output\users.json is not valid JSON: Expecting  ::
::      property name enclosed in double quotes: line 1 column 2      ::
::      (char 1)                                                      ::
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
```

### 8. See the logs

Every run writes detailed log lines to `output/importer.log`. Show the last ones, or add `-v` to also see them in the terminal:

```bash
Get-Content output\importer.log -Tail 10
```
```bash
python -m poetry run python -m importer.cli data/sample_users.csv -v
```

### Clean up

Delete the database so the next run starts fresh:

```bash
Remove-Item output\users.json
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
│   ├── cli.py               # entry point (main), arguments, exit codes
│   ├── display.py           # result and error boxes printed in the terminal
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
            <── ImportSummary ──> display.format_report()
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
terminal (stderr).

## Testing and coverage

```bash
# Run all tests
python -m poetry run python -m pytest

# Run with coverage (fails if coverage drops below 90%)
python -m poetry run python -m pytest --cov --cov-report=term-missing

# Optional HTML report in htmlcov/
python -m poetry run python -m pytest --cov --cov-report=html
```

**18 tests, 96% line and branch coverage** (see
[`reports/coverage.txt`](reports/coverage.txt)).

| Test file | Covers | Techniques |
|---|---|---|
| `test_parser.py` | valid and invalid CSV files, missing file, file system error | parametrize, `tmp_path`, mocker |
| `test_validator.py` | valid row, invalid rows | parametrize |
| `test_repository.py` | save and load, duplicate user, failed write | `tmp_path`, mocker |
| `test_service.py` | valid row saved, missing CSV saves nothing (all parts mocked) | pytest-mock (`create_autospec`) |
| `test_integration.py` | real files end to end through the CLI | no mocks |

Shared fixtures in `tests/conftest.py` provide temporary CSV files, a temporary
database path and a mock repository; `tests/helpers.py` builds sample rows.

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
