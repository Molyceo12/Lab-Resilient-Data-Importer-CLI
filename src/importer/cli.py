"""Command-line interface: ``python -m importer.cli data/sample_users.csv``."""

from __future__ import annotations

import argparse
import logging
import time
from collections.abc import Sequence

from importer.display import render_error, render_report
from importer.exceptions import ImporterError
from importer.logging_config import VALID_LEVELS, configure_logging
from importer.parser import CsvParser
from importer.repository import JsonUserRepository
from importer.service import ImportService
from importer.validator import UserValidator

logger = logging.getLogger(__name__)
DEFAULT_DB_PATH = "output/users.json"
DEFAULT_LOG_FILE = "output/importer.log"
EXIT_OK, EXIT_FATAL, EXIT_PARTIAL = 0, 1, 2


def build_arg_parser() -> argparse.ArgumentParser:
    """Return the command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="importer",
        description="Import users from a CSV file into a JSON database.",
        epilog="Exit codes: 0 = all imported, 1 = fatal error, "
        "2 = finished with skipped rows.",
    )
    parser.add_argument("csv_file", help="path to the CSV file to import")
    parser.add_argument(
        "--db",
        default=DEFAULT_DB_PATH,
        help=f"path to the JSON database (default: {DEFAULT_DB_PATH})",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        type=str.upper,
        choices=VALID_LEVELS,
        help="logging detail (default: INFO)",
    )
    parser.add_argument(
        "--log-file",
        default=DEFAULT_LOG_FILE,
        help=f"file to write detailed logs to (default: {DEFAULT_LOG_FILE})",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="also print detailed log lines in the terminal",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the importer and return the exit code (0 ok, 1 fatal, 2 skipped rows)."""
    args = build_arg_parser().parse_args(argv)
    configure_logging(args.log_level, log_file=args.log_file, console=args.verbose)
    service = ImportService(CsvParser(), UserValidator(), JsonUserRepository(args.db))
    started = time.perf_counter()
    try:
        summary = service.run(args.csv_file)
    except ImporterError as exc:
        logger.error("Import failed: %s", exc)
        print(render_error(exc, args.csv_file))
        return EXIT_FATAL
    elapsed = time.perf_counter() - started
    print(render_report(summary, args.csv_file, args.db, args.log_file, elapsed))
    return EXIT_PARTIAL if summary.has_problems else EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
