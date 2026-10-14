"""Tests for the JSON user repository."""

import json
from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from importer.exceptions import DuplicateUserError, StorageError
from importer.models import User
from importer.repository import JsonUserRepository, UserRepository, atomic_write

BOB = User(user_id="U2", name="Bob", email="bob@example.com")


def write_json(path: Path, data: object) -> None:
    """Write raw JSON data to a file, creating its folder."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


def test_interface_cannot_be_instantiated() -> None:
    with pytest.raises(TypeError):
        UserRepository()  # type: ignore[abstract]


def test_missing_file_starts_empty(db_path: Path) -> None:
    assert JsonUserRepository(db_path).get_all() == []
    assert not db_path.exists()


def test_add_and_save_round_trip(db_path: Path, sample_user: User) -> None:
    repository = JsonUserRepository(db_path)
    repository.add(sample_user)
    repository.add(BOB)
    repository.save()

    assert json.loads(db_path.read_text(encoding="utf-8")) == [
        sample_user.to_dict(),
        BOB.to_dict(),
    ]
    assert JsonUserRepository(db_path).get_all() == [sample_user, BOB]


def test_get_all_includes_unsaved_users(db_path: Path, sample_user: User) -> None:
    repository = JsonUserRepository(db_path)
    repository.add(sample_user)
    assert repository.get_all() == [sample_user]
    assert not db_path.exists()


def test_accepts_string_path(tmp_path: Path, sample_user: User) -> None:
    repository = JsonUserRepository(str(tmp_path / "users.json"))
    repository.add(sample_user)
    repository.save()
    assert (tmp_path / "users.json").exists()


@pytest.mark.parametrize(
    ("duplicate", "field"),
    [
        pytest.param(
            User("U1", "Someone Else", "other@example.com"), "user_id", id="same-id"
        ),
        pytest.param(User("U9", "Alice Two", "alice@example.com"), "email", id="email"),
        pytest.param(
            User("U9", "Alice Caps", "ALICE@Example.com"), "email", id="email-case"
        ),
    ],
)
def test_rejects_duplicates(
    db_path: Path, sample_user: User, duplicate: User, field: str
) -> None:
    repository = JsonUserRepository(db_path)
    repository.add(sample_user)

    with pytest.raises(DuplicateUserError) as caught:
        repository.add(duplicate)

    assert caught.value.field == field
    assert repository.get_all() == [sample_user]


def test_detects_duplicates_from_existing_file(
    db_path: Path, sample_user: User
) -> None:
    write_json(db_path, [sample_user.to_dict()])
    repository = JsonUserRepository(db_path)

    with pytest.raises(DuplicateUserError):
        repository.add(User("U5", "New", "alice@example.com"))

    repository.add(BOB)
    assert repository.get_all() == [sample_user, BOB]


@pytest.mark.parametrize(
    ("content", "message"),
    [
        pytest.param("{oops", "is not valid JSON", id="corrupt"),
        pytest.param('{"user_id": "U1"}', "must contain a JSON list", id="object"),
        pytest.param("[1]", "invalid record at index 0", id="not-an-object"),
        pytest.param(
            '[{"user_id": "U1", "name": "A"}]',
            "invalid record at index 0",
            id="missing-field",
        ),
        pytest.param(
            '[{"user_id": "U1", "name": "A", "email": "a@x.com"},'
            ' {"user_id": 2, "name": "B", "email": "b@x.com"}]',
            "invalid record at index 1",
            id="wrong-type",
        ),
    ],
)
def test_rejects_bad_database_files(db_path: Path, content: str, message: str) -> None:
    db_path.parent.mkdir(parents=True)
    db_path.write_text(content, encoding="utf-8")

    with pytest.raises(StorageError, match=message):
        JsonUserRepository(db_path).get_all()


def test_unreadable_database_raises(tmp_path: Path) -> None:
    folder = tmp_path / "not-a-file"
    folder.mkdir()

    with pytest.raises(StorageError, match="Cannot read database"):
        JsonUserRepository(folder).get_all()


def test_write_failure_keeps_old_file(
    db_path: Path, sample_user: User, mocker: MockerFixture
) -> None:
    write_json(db_path, [sample_user.to_dict()])
    before = db_path.read_bytes()
    repository = JsonUserRepository(db_path)
    repository.add(BOB)
    mocker.patch("importer.repository.os.replace", side_effect=OSError("disk full"))

    with pytest.raises(StorageError, match="Cannot write database"):
        repository.save()

    assert db_path.read_bytes() == before
    assert list(db_path.parent.glob("*.tmp")) == []


def test_atomic_write_replaces_file(tmp_path: Path) -> None:
    target = tmp_path / "new" / "data.txt"
    with atomic_write(target) as handle:
        handle.write("hello")

    assert target.read_text(encoding="utf-8") == "hello"
    assert list(target.parent.glob("*.tmp")) == []


def test_atomic_write_error_leaves_target_untouched(tmp_path: Path) -> None:
    target = tmp_path / "data.txt"
    target.write_text("original", encoding="utf-8")

    with pytest.raises(RuntimeError), atomic_write(target) as handle:
        handle.write("half written")
        raise RuntimeError("crash")

    assert target.read_text(encoding="utf-8") == "original"
    assert list(tmp_path.glob("*.tmp")) == []
