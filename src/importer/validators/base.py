"""Validator interface (Dependency Inversion)."""

from abc import ABC, abstractmethod

from importer.models import User
from importer.parsers import RawRow


class RowValidator(ABC):
    """What any validator must do; the service depends only on this."""

    @abstractmethod
    def validate(self, row: RawRow) -> User:
        """Return a ``User`` built from the row.

        Raises:
            ValidationError: If the row data is invalid.
        """
