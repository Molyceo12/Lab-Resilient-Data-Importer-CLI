"""Tests for the JSON user repository."""

import json
from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from importer.exceptions import DuplicateUserError, StorageError
from importer.models import User
from importer.repository import JsonUserRepository, UserRepository, atomic_write

ALICE = User("U1", "Alice", "alice@example.com")
BOB = User("U2", "Bob", "bob@example.com")


def test_interface_is_abstract() -> None:
    with pytest.raises(TypeError):
        UserRepository()  # type: ignore[abstract]  # pylint: disable=abstract-class-instantiated


def test_save_and_load(db_path: Path) -> None:
    repository = JsonUserRepository(db_path)
    assert not repository.users  # no file yet
    repository.add(ALICE)
    repository.save()
    reloaded = JsonUserRepository(db_path)
    reloaded.add(BOB)
    assert list(reloaded.users.values()) == [ALICE, BOB]
    assert json.loads(db_path.read_text(encoding="utf-8")) == [ALICE.to_dict()]


@pytest.mark.parametrize(
    ("duplicate", "field"),
    [
        (User("U1", "Other", "other@example.com"), "user_id"),
        (User("U9", "Alice2", "ALICE@Example.com"), "email"),
    ],
)
def test_rejects_duplicates(db_path: Path, duplicate: User, field: str) -> None:
    repository = JsonUserRepository(db_path)
    repository.add(ALICE)
    with pytest.raises(DuplicateUserError) as caught:
        repository.add(duplicate)
    assert caught.value.field == field


@pytest.mark.parametrize(
    ("content", "message"),
    [
        ("{oops", "is not valid JSON"),
        ('{"user_id": "U1"}', "has invalid user records"),
        ('[{"user_id": "U1"}]', "has invalid user records"),
    ],
)
def test_rejects_bad_database_files(db_path: Path, content: str, message: str) -> None:
    db_path.parent.mkdir(parents=True)
    db_path.write_text(content, encoding="utf-8")
    with pytest.raises(StorageError, match=message):
        _ = JsonUserRepository(db_path).users


def test_unreadable_database(tmp_path: Path) -> None:
    with pytest.raises(StorageError, match="Cannot read database"):
        _ = JsonUserRepository(tmp_path).users  # a folder, not a file


def test_failed_write_keeps_old_file(db_path: Path, mocker: MockerFixture) -> None:
    db_path.parent.mkdir(parents=True)
    db_path.write_text("[]", encoding="utf-8")
    repository = JsonUserRepository(db_path)
    repository.add(ALICE)
    mocker.patch("importer.repository.os.replace", side_effect=OSError("disk full"))
    with pytest.raises(StorageError, match="Cannot write database"):
        repository.save()
    assert db_path.read_text(encoding="utf-8") == "[]"
    assert not list(db_path.parent.glob("*.tmp"))


def test_atomic_write_error_leaves_target_untouched(tmp_path: Path) -> None:
    target = tmp_path / "data.txt"
    target.write_text("original", encoding="utf-8")
    with pytest.raises(RuntimeError), atomic_write(target) as handle:
        handle.write("half written")
        raise RuntimeError("crash")
    assert target.read_text(encoding="utf-8") == "original"
    assert not list(tmp_path.glob("*.tmp"))
