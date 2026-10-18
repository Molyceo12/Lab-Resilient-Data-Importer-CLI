"""User data model."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class User:
    """A user record: id, name and email (email stored lowercase)."""

    user_id: str
    name: str
    email: str

    def to_dict(self) -> dict[str, str]:
        """Return the user as a dictionary for JSON."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> User:
        """Return a user built from a JSON dictionary."""
        return cls(data["user_id"], data["name"], data["email"])
