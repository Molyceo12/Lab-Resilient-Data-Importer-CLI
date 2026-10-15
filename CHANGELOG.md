# Changelog

All notable changes to this project are listed here.
The format follows [Keep a Changelog](https://keepachangelog.com/) and the
project uses [Semantic Versioning](https://semver.org/).

## [1.0.0] - 2026-10-15

First release.

### Added
- CLI that imports users (`user_id`, `name`, `email`) from a CSV file into a
  JSON database: `python -m importer.cli <csv_file>`
- Options `--db`, `--log-level`, `--log-file` and `-v/--verbose`
- Exit codes: `0` all imported, `1` fatal error, `2` some rows skipped
- Custom exception hierarchy: `ImporterError`, `CsvFileNotFoundError`,
  `FileFormatError`, `ValidationError`, `DuplicateUserError`, `StorageError`
- CSV parser with a context manager; accepts any header order, letter case,
  a UTF-8 BOM and blank lines
- Row validation: column count, empty fields, name length, email format
- Duplicate detection by `user_id` or email (case-insensitive)
- JSON repository with atomic writes, so the database is never half-written
- Boxed terminal report with a problems table, and an error box with tips
- Structured logging to `output/importer.log`
- Sample data: `data/sample_users.csv` and `data/invalid_users.csv`
- Test suite: 127 tests (unit and integration) with fixtures, parametrize and
  pytest-mock; 100% line and branch coverage (`reports/coverage.txt`)
- Code quality: Black, ruff, mypy (strict) and pre-commit hooks; Pylint clean
- README with setup, usage, design and testing instructions

[1.0.0]: https://github.com/Molyceo12/Lab-Resilient-Data-Importer-CLI/releases/tag/v1.0.0
