"""
Test the csv_to_sqlite script.
Generated via GPT-5-Codex in Cursor.
"""

import sqlite3
import tempfile
from pathlib import Path

import unittest


class TestCSVToSQLite(unittest.TestCase):
    def test_convert_csv_creates_database_with_expected_table_and_rows(self):
        from backend.scripts.csv_to_sqlite import convert_csv_to_sqlite

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            csv_path = tmpdir_path / "source.csv"
            csv_path.write_text("id,name\n1,Alice\n2,Bob\n", encoding="utf-8")

            db_path = tmpdir_path / "output.db"

            result = convert_csv_to_sqlite(str(db_path), str(csv_path))

            self.assertEqual(result["table_name"], "source")
            self.assertEqual(result["rows_inserted"], 2)
            self.assertTrue(db_path.exists())

            with sqlite3.connect(db_path) as conn:
                tables = {
                    row[0]
                    for row in conn.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    ).fetchall()
                }
                self.assertIn("source", tables)

                columns = [row[1] for row in conn.execute("PRAGMA table_info(source)")]
                self.assertEqual(columns, ["id", "name"])

                rows = conn.execute("SELECT * FROM source ORDER BY id").fetchall()
                self.assertEqual(rows, [("1", "Alice"), ("2", "Bob")])

    def test_multiple_csv_files_create_multiple_tables_in_same_database(self):
        from backend.scripts.csv_to_sqlite import convert_csv_to_sqlite

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            first_csv = tmpdir_path / "first.csv"
            second_csv = tmpdir_path / "second.csv"

            first_csv.write_text("id,value\n1,foo\n2,bar\n", encoding="utf-8")
            second_csv.write_text("id,value\n3,baz\n4,qux\n", encoding="utf-8")

            db_path = tmpdir_path / "output.db"

            first_result = convert_csv_to_sqlite(str(db_path), str(first_csv))
            second_result = convert_csv_to_sqlite(str(db_path), str(second_csv))

            self.assertEqual(first_result["table_name"], "first")
            self.assertEqual(second_result["table_name"], "second")

            with sqlite3.connect(db_path) as conn:
                tables = {
                    row[0]
                    for row in conn.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    ).fetchall()
                }
                self.assertEqual(tables, {"first", "second"})

                first_rows = conn.execute(
                    "SELECT * FROM first ORDER BY id"
                ).fetchall()
                second_rows = conn.execute(
                    "SELECT * FROM second ORDER BY id"
                ).fetchall()

                self.assertEqual(first_rows, [("1", "foo"), ("2", "bar")])
                self.assertEqual(second_rows, [("3", "baz"), ("4", "qux")])


if __name__ == "__main__":
    unittest.main()

