"""CSV reading: the parser only reads rows; the validator checks them."""

import csv
import logging
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import TextIO

from importer.exceptions import CsvFileNotFoundError, FileFormatError
from importer.parsers.base import RawRow, RowParser

logger = logging.getLogger(__name__)
REQUIRED_HEADERS = ["user_id", "name", "email"]


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


class CsvParser(RowParser):
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
            reader = csv.reader(file)  # reads one line at a time
            try:
                first_line = next(reader, None)
                if first_line is None:
                    raise FileFormatError(f"CSV file is empty: {csv_path}")

                headers = [name.strip().lower() for name in first_line]
                for name in REQUIRED_HEADERS:
                    if name not in headers:
                        raise FileFormatError(
                            f"CSV file is missing required headers: {name}"
                        )

                for values in reader:
                    if not any(value.strip() for value in values):
                        continue  # skip blank lines

                    data = {}
                    for i, header in enumerate(headers):
                        if i < len(values):
                            data[header] = values[i].strip()
                        else:
                            data[header] = ""

                    yield RawRow(reader.line_num, data, len(values), len(headers))
            except (csv.Error, UnicodeDecodeError) as error:
                raise FileFormatError(f"Cannot read CSV file {csv_path}") from error
            else:
                logger.info("Finished reading %s", csv_path)
            finally:
                logger.debug("Closed CSV file %s", csv_path)
