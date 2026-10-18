"""Import result models."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class RowProblem:
    """A CSV row that was not imported: line, kind and details."""

    line_number: int
    kind: str
    details: str


@dataclass
class ImportSummary:
    """Counts and problems collected during one import run."""

    imported: int = 0
    skipped: int = 0
    duplicates: int = 0
    problems: list[RowProblem] = field(default_factory=list)

    @property
    def has_problems(self) -> bool:
        """Return ``True`` if any row was skipped or duplicated."""
        return self.skipped + self.duplicates > 0
