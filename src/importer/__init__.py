"""Resilient Data Importer: import users from CSV into a JSON database.

The package is split into folders, each with one job:

- ``parsers``: reads raw rows from a CSV file
- ``validators``: turns raw rows into ``User`` objects
- ``repositories``: the storage interface and its JSON implementation
- ``services``: runs parse, validate and store for one file
- ``models``: the ``User``, ``ImportSummary`` and ``RowProblem`` dataclasses
- ``utils``: terminal output, logging setup and atomic file writes
- ``cli``: the command-line entry point
"""

__version__ = "2.0.0"
