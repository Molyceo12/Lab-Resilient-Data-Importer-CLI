"""User storage: the repository interface and its JSON implementation."""

from importer.repositories.base import UserRepository
from importer.repositories.json_repository import JsonUserRepository

__all__ = ["JsonUserRepository", "UserRepository"]
