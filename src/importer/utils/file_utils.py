"""File helpers shared across the importer."""

import os
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import TextIO


@contextmanager
def atomic_write(path: Path) -> Iterator[TextIO]:
    """Write to a temp file that replaces ``path`` only if writing succeeds."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        # Pylint in VS Code wrongly infers None here; open() is a context manager.
        # pylint: disable-next=not-context-manager
        with open(fd, "w", encoding="utf-8") as handle:
            yield handle
        os.replace(tmp, path)
    finally:
        Path(tmp).unlink(missing_ok=True)  # already gone after a successful replace
