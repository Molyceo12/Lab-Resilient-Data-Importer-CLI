"""CSV reading: the parser only reads rows; the validator checks them."""

import csv
import logging
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO

from importer.exceptions import CsvFileNotFoundError, FileFormatError

logger = logging.getLogger(__name__)
REQUIRED_HEADERS = ["user_id", "name", "email"]


@dataclass(frozen=True)
class RawRow:
    """One row from the CSV file, not checked yet."""

    line_number: int
    data: dict[str, str]
    column_count: int
    expected_columns: int


@contextmanager
def open_csv(path: Path) -> Iterator[TextIO]:
    """Open a CSV file for reading and always close it afterwards.

    Raises:
        CsvFileNotFoundError: If the file does not exist.
        FileFormatError: If the file exists but cannot be opened.
    """
    try:
        file = path.open(encoding="utf-8-sig", newline="")
    except FileNotFoundError as error:
        raise CsvFileNotFoundError(f"CSV file not found: {path}") from error
    except OSError as error:
        raise FileFormatError(f"Cannot open CSV file {path}: {error}") from error
    with file:
        yield file


class CsvParser:
    """Reads user rows from a CSV file."""

    def parse(self, path: str | Path) -> Iterator[RawRow]:
        """Yield every non-empty data row of the CSV file.

        Raises:
            CsvFileNotFoundError: If the file does not exist.
            FileFormatError: If the file is empty, unreadable or misses headers.
        """
        csv_path = Path(path)
        logger.info("Reading CSV file %s", csv_path)

        with open_csv(csv_path) as file:
            try:
                lines = list(csv.reader(file))
            except (csv.Error, UnicodeDecodeError) as error:
                raise FileFormatError(f"Cannot read CSV file {csv_path}") from error
            else:
                logger.info("Read %d lines from %s", len(lines), csv_path)
            finally:
                logger.debug("Finished reading %s", csv_path)

        if not lines:
            raise FileFormatError(f"CSV file is empty: {csv_path}")

        headers = [name.strip().lower() for name in lines[0]]
        for name in REQUIRED_HEADERS:
            if name not in headers:
                raise FileFormatError(f"CSV file is missing required headers: {name}")

        line_number = 1
        for values in lines[1:]:
            line_number += 1
            if not any(value.strip() for value in values):
                continue  # skip blank lines

            data = {}
            for i, header in enumerate(headers):
                if i < len(values):
                    data[header] = values[i].strip()
                else:
                    data[header] = ""

            yield RawRow(line_number, data, len(values), len(headers))
