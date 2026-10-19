"""JSON file implementation of the user repository."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from importer.exceptions import DuplicateUserError, StorageError
from importer.models import User
from importer.repositories.base import UserRepository
from importer.utils.file_utils import atomic_write

logger = logging.getLogger(__name__)


class JsonUserRepository(UserRepository):
    """Stores users in a JSON list; loads the file once and saves once."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._users: dict[str, User] | None = None

    @property
    def users(self) -> dict[str, User]:
        """Return stored users by id, loading the file on first use.

        Raises:
            StorageError: If the file is unreadable or not a list of users.
        """
        if self._users is None:
            self._users = {user.user_id: user for user in self._read()}
        return self._users

    def add(self, user: User) -> None:
        """Add a user in memory; call ``save`` to persist.

        Raises:
            DuplicateUserError: If the user id or email is already stored.
        """
        if user.user_id in self.users:
            raise DuplicateUserError(user.user_id, "user_id")
        if any(u.email.lower() == user.email.lower() for u in self.users.values()):
            raise DuplicateUserError(user.user_id, "email")
        self.users[user.user_id] = user

    def save(self) -> None:
        """Write all users to the JSON file atomically.

        Raises:
            StorageError: If the file cannot be written.
        """
        records = [user.to_dict() for user in self.users.values()]
        try:
            with atomic_write(self.path) as handle:
                json.dump(records, handle, indent=2, ensure_ascii=False)
                handle.write("\n")
        except OSError as exc:
            raise StorageError(f"Cannot write database {self.path}: {exc}") from exc
        logger.info("Saved %d users to %s", len(records), self.path)

    def _read(self) -> list[User]:
        """Read the users saved in the JSON file (none if it does not exist)."""
        if not self.path.exists():
            logger.info("Database %s not found; starting empty", self.path)
            return []
        try:
            with self.path.open(encoding="utf-8") as handle:
                users = [User.from_dict(record) for record in json.load(handle)]
        except json.JSONDecodeError as exc:
            raise StorageError(
                f"Database {self.path} is not valid JSON: {exc}"
            ) from exc
        except OSError as exc:
            raise StorageError(f"Cannot read database {self.path}: {exc}") from exc
        except (TypeError, KeyError) as exc:
            raise StorageError(
                f"Database {self.path} has invalid user records"
            ) from exc
        logger.info("Loaded %d existing users from %s", len(users), self.path)
        return users
