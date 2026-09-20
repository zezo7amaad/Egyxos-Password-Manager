"""Safely inspect a legacy EGYXOS vault before a client-side migration.

This tool intentionally does not print or upload vault secrets. Decryption and
re-encryption must be performed locally by a future migration workflow after
the user explicitly supplies the legacy unlock credential.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path


def inspect_database(path: Path) -> dict[str, object]:
    if not path.is_file():
        raise FileNotFoundError(path)
    with sqlite3.connect(path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
            )
        }
        if "vault" not in tables:
            raise ValueError("legacy database does not contain a vault table")
        columns = [row[1] for row in connection.execute("PRAGMA table_info(vault)")]
        count = connection.execute("SELECT COUNT(*) FROM vault").fetchone()
        return {
            "source": str(path.resolve()),
            "tables": sorted(tables),
            "vault_columns": columns,
            "record_count": int(count[0]) if count else 0,
            "migration_status": "inspection-only; no secrets were decrypted",
        }


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect a legacy EGYXOS SQLite vault")
    parser.add_argument("database", type=Path)
    args = parser.parse_args()
    print(json.dumps(inspect_database(args.database), indent=2))


if __name__ == "__main__":
    main()
