"""User storage interface (repository pattern)."""

from abc import ABC, abstractmethod

from importer.models import User


class UserRepository(ABC):
    """What any user storage must do; the service depends only on this."""

    @abstractmethod
    def add(self, user: User) -> None:
        """Add a user, raising ``DuplicateUserError`` if id or email exists."""

    @abstractmethod
    def save(self) -> None:
        """Persist all users, raising ``StorageError`` on failure."""
