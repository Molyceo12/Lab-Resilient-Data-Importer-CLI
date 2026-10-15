"""Tests for the data models."""

import dataclasses

import pytest

from importer.models import ImportSummary, User


def test_user_round_trip_and_frozen() -> None:
    user = User("U1", "Alice", "alice@example.com")
    assert user.to_dict() == {
        "user_id": "U1",
        "name": "Alice",
        "email": "alice@example.com",
    }
    assert User.from_dict(user.to_dict()) == user
    with pytest.raises(dataclasses.FrozenInstanceError):
        user.name = "Bob"  # type: ignore[misc]


@pytest.mark.parametrize(
    ("counts", "total", "has_problems"),
    [
        ((0, 0, 0), 0, False),
        ((5, 0, 0), 5, False),
        ((2, 1, 0), 3, True),
        ((0, 0, 2), 2, True),
    ],
)
def test_summary_totals(
    counts: tuple[int, int, int], total: int, has_problems: bool
) -> None:
    summary = ImportSummary(*counts)
    assert summary.total_rows == total
    assert summary.has_problems is has_problems
    assert not summary.problems
