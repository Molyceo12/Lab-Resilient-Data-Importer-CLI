"""Parser interface and the raw row it produces."""

from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RawRow:
    """One row from the input file, not checked yet."""

    line_number: int
    data: dict[str, str]
    column_count: int
    expected_columns: int


class RowParser(ABC):
    """What any parser must do; the service depends only on this."""

    @abstractmethod
    def parse(self, path: str | Path) -> Iterator[RawRow]:
        """Yield the data rows of the file.

        Raises:
            CsvFileNotFoundError: If the file does not exist.
            FileFormatError: If the file is empty, unreadable or misses headers.
        """
