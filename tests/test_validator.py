"""Tests for the user validator."""

import pytest

from importer.exceptions import ValidationError
from importer.models import User
from importer.parser import RawRow
from importer.validator import MAX_NAME_LENGTH, UserValidator
from tests.helpers import RowFactory


@pytest.fixture(name="validator")
def fixture_validator() -> UserValidator:
    """Return a validator instance."""
    return UserValidator()


def test_valid_row_becomes_user(validator: UserValidator, make_row: RowFactory) -> None:
    user = validator.validate(make_row())
    assert user == User(user_id="U1", name="Alice", email="alice@example.com")


def test_values_are_trimmed_and_email_lowercased(
    validator: UserValidator, make_row: RowFactory
) -> None:
    user = validator.validate(make_row(" U1 ", "  Alice ", " Alice@Example.COM "))
    assert user == User(user_id="U1", name="Alice", email="alice@example.com")


@pytest.mark.parametrize(
    "email",
    ["a@b.co", "first.last@example.com", "user+tag@mail.example.org", "x_y@d-1.io"],
)
def test_accepts_valid_emails(
    validator: UserValidator, make_row: RowFactory, email: str
) -> None:
    assert validator.validate(make_row(email=email)).email == email


def test_accepts_name_at_max_length(
    validator: UserValidator, make_row: RowFactory
) -> None:
    name = "N" * MAX_NAME_LENGTH
    assert validator.validate(make_row(name=name)).name == name


@pytest.mark.parametrize(
    ("values", "field", "reason"),
    [
        pytest.param(("", "Alice", "a@x.com"), "user_id", "value is empty", id="no-id"),
        pytest.param(("U1", "", "a@x.com"), "name", "value is empty", id="no-name"),
        pytest.param(("U1", "   ", "a@x.com"), "name", "value is empty", id="blank"),
        pytest.param(("U1", "Alice", ""), "email", "value is empty", id="no-email"),
        pytest.param(("U1", "Alice", "bob"), "email", "is not valid", id="no-at"),
        pytest.param(("U1", "Alice", "bob@"), "email", "is not valid", id="no-domain"),
        pytest.param(("U1", "Alice", "@x.com"), "email", "is not valid", id="no-user"),
        pytest.param(("U1", "Alice", "bob@x"), "email", "is not valid", id="no-tld"),
        pytest.param(
            ("U1", "Alice", "b ob@x.com"), "email", "is not valid", id="space"
        ),
        pytest.param(
            ("U1", "Alice", "a@@x.com"), "email", "is not valid", id="two-ats"
        ),
        pytest.param(
            ("U1", "N" * (MAX_NAME_LENGTH + 1), "a@x.com"),
            "name",
            f"longer than {MAX_NAME_LENGTH} characters",
            id="name-too-long",
        ),
    ],
)
def test_rejects_invalid_values(
    validator: UserValidator,
    make_row: RowFactory,
    values: tuple[str, str, str],
    field: str,
    reason: str,
) -> None:
    with pytest.raises(ValidationError) as caught:
        validator.validate(make_row(*values, line_number=9))

    assert caught.value.line_number == 9
    assert caught.value.field == field
    assert reason in caught.value.reason


@pytest.mark.parametrize("column_count", [2, 4])
def test_rejects_wrong_column_count(
    validator: UserValidator, make_row: RowFactory, column_count: int
) -> None:
    with pytest.raises(ValidationError) as caught:
        validator.validate(make_row(column_count=column_count))

    assert caught.value.field == "row"
    assert caught.value.reason == f"expected 3 columns, got {column_count}"


def test_missing_field_key_counts_as_empty(validator: UserValidator) -> None:
    row = RawRow(
        line_number=4, data={"name": "Alice"}, column_count=1, expected_columns=1
    )

    with pytest.raises(ValidationError) as caught:
        validator.validate(row)

    assert caught.value.field == "user_id"
