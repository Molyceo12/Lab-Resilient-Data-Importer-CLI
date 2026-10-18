"""Tests for the JSON user repository."""

from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from importer.exceptions import DuplicateUserError, StorageError
from importer.models import User
from importer.repository import JsonUserRepository

ALICE = User("U1", "Alice", "alice@example.com")


def test_save_and_load(db_path: Path) -> None:
    """A saved user is loaded back from the JSON file."""
    repository = JsonUserRepository(db_path)
    repository.add(ALICE)
    repository.save()
    assert JsonUserRepository(db_path).users == {"U1": ALICE}


def test_rejects_duplicate_user(db_path: Path) -> None:
    """Adding the same user twice raises DuplicateUserError."""
    repository = JsonUserRepository(db_path)
    repository.add(ALICE)
    with pytest.raises(DuplicateUserError):
        repository.add(ALICE)


def test_failed_save(db_path: Path, mocker: MockerFixture) -> None:
    """If writing the file fails, StorageError is raised."""
    mocker.patch("importer.repository.os.replace", side_effect=OSError("disk full"))
    repository = JsonUserRepository(db_path)
    repository.add(ALICE)
    with pytest.raises(StorageError, match="Cannot write database"):
        repository.save()
