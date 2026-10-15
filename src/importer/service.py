"""Import service: runs parse → validate → store for one CSV file."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from importer.exceptions import DuplicateUserError, ValidationError
from importer.models import ImportSummary, RowProblem
from importer.parser import CsvParser
from importer.repository import UserRepository
from importer.validator import UserValidator

logger = logging.getLogger(__name__)


@dataclass
class ImportService:
    """Coordinates the parser, validator and repository (passed in, so mockable)."""

    parser: CsvParser
    validator: UserValidator
    repository: UserRepository

    def run(self, csv_path: str | Path) -> ImportSummary:
        """Import every valid user; skip and record bad or duplicate rows.

        Raises:
            CsvFileNotFoundError: If the CSV file does not exist.
            FileFormatError: If the CSV file is empty, unreadable or misses headers.
            StorageError: If the database cannot be read or written.
        """
        summary = ImportSummary()
        logger.info("Starting import from %s", csv_path)
        try:
            for row in self.parser.parse(csv_path):
                try:
                    user = self.validator.validate(row)
                    self.repository.add(user)
                except ValidationError as exc:
                    summary.skipped += 1
                    details = f"{exc.field}: {exc.reason}"
                    summary.problems.append(
                        RowProblem(exc.line_number, "invalid", details)
                    )
                    logger.warning("Skipped row: %s", exc)
                except DuplicateUserError as exc:
                    summary.duplicates += 1
                    details = f"{exc.field} already exists (user {exc.user_id})"
                    summary.problems.append(
                        RowProblem(row.line_number, "duplicate", details)
                    )
                    logger.warning(
                        "Skipped duplicate at line %d: %s", row.line_number, exc
                    )
                else:
                    summary.imported += 1
                    logger.info("Imported user %s", user.user_id)
            self.repository.save()
        finally:
            logger.info(
                "Import finished: %d imported, %d skipped, %d duplicates",
                summary.imported,
                summary.skipped,
                summary.duplicates,
            )
        return summary
