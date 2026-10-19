"""Row validation: turns raw CSV rows into ``User`` objects."""

import re

from importer.exceptions import ValidationError
from importer.models import User
from importer.parsers import RawRow

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MAX_NAME_LENGTH = 100


class UserValidator:
    """Checks a raw CSV row and builds a ``User`` from it."""

    def validate(self, row: RawRow) -> User:
        """Return a ``User`` with trimmed values and a lowercase email.

        Raises:
            ValidationError: If the column count, a required field, the name
                length or the email format is wrong.
        """
        if row.column_count != row.expected_columns:
            reason = f"expected {row.expected_columns} columns, got {row.column_count}"
            raise ValidationError(row.line_number, "row", reason)
        user_id, name, email = (
            row.data.get(field, "").strip() for field in ("user_id", "name", "email")
        )
        for field, value in (("user_id", user_id), ("name", name), ("email", email)):
            if not value:
                raise ValidationError(row.line_number, field, "value is empty")
        if len(name) > MAX_NAME_LENGTH:
            reason = f"longer than {MAX_NAME_LENGTH} characters"
            raise ValidationError(row.line_number, "name", reason)
        if not EMAIL_PATTERN.fullmatch(email := email.lower()):
            raise ValidationError(row.line_number, "email", f"'{email}' is not valid")
        return User(user_id, name, email)
