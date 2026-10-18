"""Custom exceptions: every expected problem is an ``ImporterError``."""


class ImporterError(Exception):
    """Base class for all importer errors."""


class CsvFileNotFoundError(ImporterError):
    """The CSV file does not exist."""


class FileFormatError(ImporterError):
    """The CSV file is empty, unreadable or has wrong headers."""


class StorageError(ImporterError):
    """The JSON database cannot be read or written."""


class ValidationError(ImporterError):
    """A CSV row contains invalid data."""

    def __init__(self, line_number: int, field: str, reason: str) -> None:
        self.line_number, self.field, self.reason = line_number, field, reason
        super().__init__(f"Line {line_number}: invalid '{field}' ({reason})")


class DuplicateUserError(ImporterError):
    """A user with the same id or email is already stored."""

    def __init__(self, user_id: str, field: str) -> None:
        self.user_id, self.field = user_id, field
        super().__init__(f"Duplicate user '{user_id}': {field} already exists")
