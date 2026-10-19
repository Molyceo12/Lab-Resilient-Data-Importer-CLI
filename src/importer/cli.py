"""Command-line interface: ``python -m importer.cli data/sample_users.csv``."""

import argparse
import logging

from importer.exceptions import ImporterError
from importer.parsers import CsvParser
from importer.repositories import JsonUserRepository
from importer.services import ImportService
from importer.utils import configure_logging, format_error, format_report
from importer.validators import UserValidator

logger = logging.getLogger(__name__)
DEFAULT_DB = "output/users.json"
DEFAULT_LOG_FILE = "output/importer.log"


def main(argv: list[str] | None = None) -> int:
    """Import the CSV file and return the exit code.

    Exit codes: 0 = all rows imported, 1 = import failed, 2 = some rows skipped.
    """
    parser = argparse.ArgumentParser(description="Import users from a CSV file.")
    parser.add_argument("csv_file", help="CSV file to import")
    parser.add_argument("--db", default=DEFAULT_DB, help="JSON database")
    parser.add_argument("--log-file", default=DEFAULT_LOG_FILE, help="log file")
    parser.add_argument("-v", "--verbose", action="store_true", help="show logs")
    args = parser.parse_args(argv)

    configure_logging(log_file=args.log_file, console=args.verbose)
    service = ImportService(CsvParser(), UserValidator(), JsonUserRepository(args.db))

    try:
        summary = service.run(args.csv_file)
    except ImporterError as error:
        logger.error("Import failed: %s", error)
        print(format_error(error, args.csv_file))
        return 1

    print(format_report(summary, args.csv_file, args.db))
    if summary.has_problems:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
