"""Small builders shared by the tests."""

from importer.parser import RawRow

VALID_CSV = "user_id,name,email\nU1,Alice,alice@example.com\nU2,Bob,bob@example.com\n"


def make_row(
    user_id: str = "U1",
    name: str = "Alice",
    email: str = "alice@example.com",
    *,
    line: int = 2,
    columns: int = 3,
) -> RawRow:
    """Build a ``RawRow`` as the parser would."""
    return RawRow(line, {"user_id": user_id, "name": name, "email": email}, columns, 3)
