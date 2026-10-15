"""Tests for the user validator."""

import pytest

from importer.exceptions import ValidationError
from importer.models import User
from importer.validator import UserValidator
from tests.helpers import make_row

LONG_NAME = "N" * 100


@pytest.mark.parametrize(
    ("values", "expected"),
    [
        (
            ("U1", "Alice", "alice@example.com"),
            User("U1", "Alice", "alice@example.com"),
        ),
        ((" U1 ", " Alice ", " A@Example.COM "), User("U1", "Alice", "a@example.com")),
        (
            ("U2", LONG_NAME, "a.b+tag@mail.co"),
            User("U2", LONG_NAME, "a.b+tag@mail.co"),
        ),
    ],
)
def test_valid_rows(values: tuple[str, str, str], expected: User) -> None:
    assert UserValidator().validate(make_row(*values)) == expected


@pytest.mark.parametrize(
    ("values", "columns", "field", "reason"),
    [
        (("U1", "Alice", "a@x.com"), 2, "row", "expected 3 columns, got 2"),
        (("", "Alice", "a@x.com"), 3, "user_id", "value is empty"),
        (("U1", "  ", "a@x.com"), 3, "name", "value is empty"),
        (("U1", "Alice", ""), 3, "email", "value is empty"),
        (("U1", LONG_NAME + "N", "a@x.com"), 3, "name", "longer than 100 characters"),
        (("U1", "Alice", "bob"), 3, "email", "'bob' is not valid"),
        (("U1", "Alice", "bob@x"), 3, "email", "'bob@x' is not valid"),
        (("U1", "Alice", "b ob@x.com"), 3, "email", "'b ob@x.com' is not valid"),
    ],
)
def test_invalid_rows(
    values: tuple[str, str, str], columns: int, field: str, reason: str
) -> None:
    with pytest.raises(ValidationError) as caught:
        UserValidator().validate(make_row(*values, line=9, columns=columns))
    assert (caught.value.line_number, caught.value.field) == (9, field)
    assert caught.value.reason == reason
