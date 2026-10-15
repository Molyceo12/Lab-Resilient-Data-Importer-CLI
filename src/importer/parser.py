"""CSV reading: the parser only reads rows; the validator judges them."""

from __future__ import annotations

import csv
import logging
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO

from importer.exceptions import CsvFileNotFoundError, FileFormatError

logger = logging.getLogger(__name__)
REQUIRED_HEADERS = ("user_id", "name", "email")


@dataclass(frozen=True)
class RawRow:
    """One unvalidated row: line number, values by header and column counts."""

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
        handle = path.open(newline="", encoding="utf-8-sig")
    except FileNotFoundError as exc:
        raise CsvFileNotFoundError(f"CSV file not found: {path}") from exc
    except OSError as exc:
        raise FileFormatError(f"Cannot open CSV file {path}: {exc}") from exc
    with handle:
        yield handle


class CsvParser:
    """Reads user rows from a CSV file."""

    def parse(self, path: str | Path) -> Iterator[RawRow]:
        """Yield every non-blank data row of a CSV file as a ``RawRow``.

        Raises:
            CsvFileNotFoundError: If the file does not exist.
            FileFormatError: If the file is empty, unreadable or misses headers.
        """
        csv_path, count = Path(path), 0
        logger.info("Reading CSV file %s", csv_path)
        with open_csv(csv_path) as handle:
            reader = csv.reader(handle)
            try:
                first = next(reader, None)
                if first is None:
                    raise FileFormatError(f"CSV file is empty: {csv_path}")
                headers = [name.strip().lower() for name in first]
                missing = [name for name in REQUIRED_HEADERS if name not in headers]
                if missing:
                    raise FileFormatError(
                        f"CSV file {csv_path} is missing required headers: "
                        + ", ".join(missing)
                    )
                for values in reader:
                    if any(value.strip() for value in values):
                        count += 1
                        padded = [*values, *[""] * len(headers)]
                        data = {h: padded[i].strip() for i, h in enumerate(headers)}
                        yield RawRow(reader.line_num, data, len(values), len(headers))
            except (csv.Error, UnicodeDecodeError) as exc:
                # Decoding happens in buffered chunks, so the line may be unknown (0).
                where = f" near line {reader.line_num}" if reader.line_num else ""
                raise FileFormatError(
                    f"Cannot read CSV file {csv_path}{where}: {exc}"
                ) from exc
            else:
                logger.info("Read %d data rows from %s", count, csv_path)
            finally:
                logger.debug("Closed CSV file %s", csv_path)
