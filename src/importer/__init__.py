"""Resilient Data Importer: import users from CSV into a JSON database.

The package is split into small parts with one job each:

- ``parser``: reads raw rows from a CSV file
- ``validator``: turns raw rows into ``User`` objects
- ``repository``: stores users in a JSON file
- ``service``: runs parse, validate and store for one file
- ``cli`` and ``display``: the command-line interface and its output
"""

__version__ = "2.0.0"
