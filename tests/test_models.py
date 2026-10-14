"""Tests for the data models."""

import dataclasses

import pytest

from importer.models import ImportSummary, RowProblem, User


def test_user_to_dict(sample_user: User) -> None:
    assert sample_user.to_dict() == {
        "user_id": "U1",
        "name": "Alice",
        "email": "alice@example.com",
    }


def test_user_round_trip(sample_user: User) -> None:
    assert User.from_dict(sample_user.to_dict()) == sample_user


def test_user_from_dict_missing_key_raises() -> None:
    with pytest.raises(KeyError):
        User.from_dict({"user_id": "U1", "name": "Alice"})


def test_user_is_frozen(sample_user: User) -> None:
    with pytest.raises(dataclasses.FrozenInstanceError):
        sample_user.name = "Changed"  # type: ignore[misc]


def test_summary_starts_empty() -> None:
    summary = ImportSummary()
    assert (summary.imported, summary.skipped, summary.duplicates) == (0, 0, 0)
    assert summary.problems == []


def test_summaries_do_not_share_problem_lists() -> None:
    first, second = ImportSummary(), ImportSummary()
    first.problems.append(RowProblem(2, "invalid", "name: value is empty"))
    assert second.problems == []


@pytest.mark.parametrize(
    ("imported", "skipped", "duplicates", "total", "has_problems"),
    [
        (0, 0, 0, 0, False),
        (5, 0, 0, 5, False),
        (2, 1, 0, 3, True),
        (2, 0, 1, 3, True),
        (0, 3, 2, 5, True),
    ],
)
def test_summary_totals(
    imported: int, skipped: int, duplicates: int, total: int, has_problems: bool
) -> None:
    summary = ImportSummary(imported=imported, skipped=skipped, duplicates=duplicates)
    assert summary.total_rows == total
    assert summary.has_problems is has_problems
