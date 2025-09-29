"""
Convert a CSV file into a SQLite database
Generated via GPT-5-Codex in Cursor.
"""

import argparse
import csv
import re
import re
import sqlite3
from pathlib import Path
from typing import Iterable, List


def convert_csv_to_sqlite(database_path: str, csv_path: str) -> dict:
    csv_file = Path(csv_path)
    db_file = Path(database_path)

    with csv_file.open(mode="r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader)
        if header is None:
            raise ValueError("CSV file must contain a header row")

        header = [column.lstrip("\ufeff") for column in header]

        rows: List[Iterable[str]] = list(reader)

    table_name = _table_name_from_path(csv_file)

    columns_definition = ", ".join(f'"{column}" TEXT' for column in header)
    insert_columns = ", ".join(f'"{column}"' for column in header)
    placeholders = ", ".join("?" for _ in header)

    with sqlite3.connect(db_file) as connection:
        cursor = connection.cursor()
        cursor.execute(f'DROP TABLE IF EXISTS "{table_name}"')
        cursor.execute(f'CREATE TABLE "{table_name}" ({columns_definition})')

        rows_inserted = 0

        if rows:
            cursor.executemany(
                f'INSERT INTO "{table_name}" ({insert_columns}) VALUES ({placeholders})',
                rows,
            )
            rows_inserted = len(rows)

        connection.commit()

    return {"table_name": table_name, "rows_inserted": rows_inserted}


def _table_name_from_path(csv_file: Path) -> str:
    stem = csv_file.stem
    sanitized = re.sub(r"\W+", "_", stem)
    return sanitized or "data"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert a CSV file into a SQLite database"
    )
    parser.add_argument("database", help="Path to the output SQLite database file")
    parser.add_argument("csv", help="Path to the source CSV file")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = convert_csv_to_sqlite(args.database, args.csv)
    print(
        f"Loaded {result['rows_inserted']} rows into table '{result['table_name']}'"
    )


if __name__ == "__main__":
    main()

