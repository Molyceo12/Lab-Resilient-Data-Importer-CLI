"""Tests for the user validator."""

import pytest

from importer.exceptions import ValidationError
from importer.models import User
from importer.parsers import RawRow
from importer.validators import UserValidator
from tests.helpers import make_row


def test_valid_row_becomes_user() -> None:
    """A good row becomes a User, with spaces trimmed and the email lowercased."""
    user = UserValidator().validate(make_row(" U1 ", "Alice", "ALICE@Example.com"))
    assert user == User("U1", "Alice", "alice@example.com")


@pytest.mark.parametrize(
    ("row", "field"),
    [
        (make_row(columns=2), "row"),  # wrong number of columns
        (make_row(name=""), "name"),  # empty name
        (make_row(email="bob"), "email"),  # bad email
    ],
)
def test_invalid_row(row: RawRow, field: str) -> None:
    """A bad row raises ValidationError naming the wrong field."""
    with pytest.raises(ValidationError, match=field):
        UserValidator().validate(row)
