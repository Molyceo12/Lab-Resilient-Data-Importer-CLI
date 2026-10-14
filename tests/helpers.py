"""Typing helpers shared by the tests."""

from pathlib import Path
from typing import Protocol

from importer.parser import RawRow


class CsvWriter(Protocol):
    """Signature of the ``write_csv`` fixture."""

    def __call__(self, content: str, name: str = ..., encoding: str = ...) -> Path: ...


class RowFactory(Protocol):
    """Signature of the ``make_row`` fixture."""

    def __call__(
        self,
        user_id: str = ...,
        name: str = ...,
        email: str = ...,
        *,
        line_number: int = ...,
        column_count: int = ...,
    ) -> RawRow: ...
