"""
Exhaustive tests for the /county_data endpoint.
Generated via GPT-5-Codex in Cursor.
"""

import sqlite3
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from backend.api.main import app, get_database_path
from backend.models.county_data import ALLOWED_MEASURES


def create_test_database(db_path: Path) -> None:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE zip_county (
            zip TEXT,
            default_state TEXT,
            county TEXT,
            county_state TEXT,
            state_abbreviation TEXT,
            county_code TEXT,
            zip_pop TEXT,
            zip_pop_in_county TEXT,
            n_counties TEXT,
            default_city TEXT
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE county_health_rankings (
            state TEXT,
            county TEXT,
            state_code TEXT,
            county_code TEXT,
            year_span TEXT,
            measure_name TEXT,
            measure_id TEXT,
            numerator TEXT,
            denominator TEXT,
            raw_value TEXT,
            confidence_interval_lower_bound TEXT,
            confidence_interval_upper_bound TEXT,
            data_release_year TEXT,
            fipscode TEXT
        )
        """
    )

    zip_rows = [
        (
            "02138",
            "MA",
            "Middlesex County",
            "MA",
            "MA",
            "17",
            "1000",
            "1000",
            "1",
            "Cambridge",
        ),
        (
            "02139",
            "MA",
            "Middlesex County",
            "MA",
            "MA",
            "17",
            "1000",
            "1000",
            "1",
            "Cambridge",
        ),
    ]

    rankings_rows = [
        (
            "MA",
            "Middlesex County",
            "25",
            "17",
            "2004",
            "Adult obesity",
            "11",
            "35658",
            "198100",
            "0.18",
            "0.17",
            "0.19",
            "",
            "25017",
        ),
        (
            "MA",
            "Middlesex County",
            "25",
            "17",
            "2005",
            "Adult obesity",
            "11",
            "44000",
            "220000",
            "0.2",
            "0.19",
            "0.21",
            "",
            "25017",
        ),
        (
            "MA",
            "Middlesex County",
            "25",
            "17",
            "2006",
            "Adult obesity",
            "11",
            "49455",
            "235500",
            "0.21",
            "0.2",
            "0.23",
            "",
            "25017",
        ),
        (
            "MA",
            "Middlesex County",
            "25",
            "17",
            "2007",
            "Adult obesity",
            "11",
            "52756",
            "239800",
            "0.22",
            "0.21",
            "0.23",
            "",
            "25017",
        ),
        (
            "MA",
            "Middlesex County",
            "25",
            "17",
            "2008",
            "Adult obesity",
            "11",
            "54362",
            "247100",
            "0.22",
            "0.21",
            "0.23",
            "2011",
            "25017",
        ),
        (
            "MA",
            "Middlesex County",
            "25",
            "17",
            "2009",
            "Adult obesity",
            "11",
            "60771.02",
            "263078",
            "0.23",
            "0.22",
            "0.24",
            "2012",
            "25017",
        ),
        (
            "MA",
            "Middlesex County",
            "25",
            "17",
            "2010",
            "Adult obesity",
            "11",
            "266426",
            "1143459.228",
            "0.233",
            "0.224",
            "0.242",
            "2014",
            "25017",
        ),
        (
            "MA",
            "Middlesex County",
            "25",
            "17",
            "2009",
            "Unemployment",
            "12",
            "100",
            "200",
            "0.5",
            "0.4",
            "0.6",
            "2012",
            "25017",
        ),
    ]

    cursor.executemany(
        "INSERT INTO zip_county VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", zip_rows
    )
    cursor.executemany(
        "INSERT INTO county_health_rankings VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        rankings_rows,
    )

    conn.commit()
    conn.close()


class TestCountyDataEndpoint(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "data.db"
        create_test_database(self.db_path)

        app.dependency_overrides[get_database_path] = lambda: self.db_path
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()
        self.temp_dir.cleanup()

    def post(self, payload: dict):
        return self.client.post("/county_data", json=payload)

    def test_successful_query_returns_expected_results(self):
        response = self.post({"zip": "02138", "measure_name": "Adult obesity"})

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIsInstance(body, list)
        self.assertEqual(len(body), 7)

        expected_keys = {
            "state",
            "county",
            "state_code",
            "county_code",
            "year_span",
            "measure_name",
            "measure_id",
            "numerator",
            "denominator",
            "raw_value",
            "confidence_interval_lower_bound",
            "confidence_interval_upper_bound",
            "data_release_year",
            "fipscode",
        }

        self.assertEqual(set(body[0].keys()), expected_keys)
        self.assertEqual(body[0]["year_span"], "2004")
        self.assertEqual(body[0]["raw_value"], "0.18")
        self.assertEqual(body[-1]["year_span"], "2010")
        self.assertEqual(body[-1]["data_release_year"], "2014")

    def test_successful_query_returns_expected_payload(self):
        response = self.post({"zip": "02138", "measure_name": "Adult obesity"})

        self.assertEqual(response.status_code, 200)
        body = response.json()

        expected = [
            {
                "state": "MA",
                "county": "Middlesex County",
                "state_code": "25",
                "county_code": "17",
                "year_span": "2004",
                "measure_name": "Adult obesity",
                "measure_id": "11",
                "numerator": "35658",
                "denominator": "198100",
                "raw_value": "0.18",
                "confidence_interval_lower_bound": "0.17",
                "confidence_interval_upper_bound": "0.19",
                "data_release_year": "",
                "fipscode": "25017",
            },
            {
                "state": "MA",
                "county": "Middlesex County",
                "state_code": "25",
                "county_code": "17",
                "year_span": "2005",
                "measure_name": "Adult obesity",
                "measure_id": "11",
                "numerator": "44000",
                "denominator": "220000",
                "raw_value": "0.2",
                "confidence_interval_lower_bound": "0.19",
                "confidence_interval_upper_bound": "0.21",
                "data_release_year": "",
                "fipscode": "25017",
            },
            {
                "state": "MA",
                "county": "Middlesex County",
                "state_code": "25",
                "county_code": "17",
                "year_span": "2006",
                "measure_name": "Adult obesity",
                "measure_id": "11",
                "numerator": "49455",
                "denominator": "235500",
                "raw_value": "0.21",
                "confidence_interval_lower_bound": "0.2",
                "confidence_interval_upper_bound": "0.23",
                "data_release_year": "",
                "fipscode": "25017",
            },
            {
                "state": "MA",
                "county": "Middlesex County",
                "state_code": "25",
                "county_code": "17",
                "year_span": "2007",
                "measure_name": "Adult obesity",
                "measure_id": "11",
                "numerator": "52756",
                "denominator": "239800",
                "raw_value": "0.22",
                "confidence_interval_lower_bound": "0.21",
                "confidence_interval_upper_bound": "0.23",
                "data_release_year": "",
                "fipscode": "25017",
            },
            {
                "state": "MA",
                "county": "Middlesex County",
                "state_code": "25",
                "county_code": "17",
                "year_span": "2008",
                "measure_name": "Adult obesity",
                "measure_id": "11",
                "numerator": "54362",
                "denominator": "247100",
                "raw_value": "0.22",
                "confidence_interval_lower_bound": "0.21",
                "confidence_interval_upper_bound": "0.23",
                "data_release_year": "2011",
                "fipscode": "25017",
            },
            {
                "state": "MA",
                "county": "Middlesex County",
                "state_code": "25",
                "county_code": "17",
                "year_span": "2009",
                "measure_name": "Adult obesity",
                "measure_id": "11",
                "numerator": "60771.02",
                "denominator": "263078",
                "raw_value": "0.23",
                "confidence_interval_lower_bound": "0.22",
                "confidence_interval_upper_bound": "0.24",
                "data_release_year": "2012",
                "fipscode": "25017",
            },
            {
                "state": "MA",
                "county": "Middlesex County",
                "state_code": "25",
                "county_code": "17",
                "year_span": "2010",
                "measure_name": "Adult obesity",
                "measure_id": "11",
                "numerator": "266426",
                "denominator": "1143459.228",
                "raw_value": "0.233",
                "confidence_interval_lower_bound": "0.224",
                "confidence_interval_upper_bound": "0.242",
                "data_release_year": "2014",
                "fipscode": "25017",
            },
        ]

        self.assertEqual(body, expected)

    def test_missing_zip_returns_bad_request(self):
        response = self.post({"measure_name": "Adult obesity"})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "Missing required field: zip")

    def test_missing_measure_name_returns_bad_request(self):
        response = self.post({"zip": "02138"})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "Missing required field: measure_name")

    def test_invalid_zip_format_returns_bad_request(self):
        response = self.post({"zip": "2138", "measure_name": "Adult obesity"})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "ZIP must be a 5-digit string")

    def test_invalid_measure_name_returns_bad_request(self):
        response = self.post({"zip": "02138", "measure_name": "Invalid Measure"})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "Invalid measure_name")

    def test_coffee_teapot_returns_418(self):
        response = self.post({"zip": "02138", "measure_name": "Adult obesity", "coffee": "teapot"})

        self.assertEqual(response.status_code, 418)
        self.assertEqual(response.json()["detail"], "I'm a teapot")

    def test_coffee_teapot_supersedes_missing_fields(self):
        response = self.post({"coffee": "teapot"})

        self.assertEqual(response.status_code, 418)

    def test_nonexistent_zip_measure_returns_not_found(self):
        response = self.post({"zip": "99999", "measure_name": "Adult obesity"})

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json()["detail"], "No data found for provided zip and measure"
        )

    def test_nonexistent_measure_for_existing_zip_returns_not_found(self):
        response = self.post({"zip": "02138", "measure_name": "Uninsured"})

        self.assertEqual(response.status_code, 404)

    def test_sql_injection_attempt_rejected(self):
        malicious_zip = "02138' OR '1'='1"
        response = self.post({"zip": malicious_zip, "measure_name": "Adult obesity"})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "ZIP must be a 5-digit string")

    def test_post_to_wrong_endpoint_returns_not_found(self):
        response = self.client.post(
            "/county_data_wrong",
            json={"zip": "02138", "measure_name": "Adult obesity"},
        )

        self.assertEqual(response.status_code, 404)

    def test_all_allowed_measures_accepted(self):
        for measure in ALLOWED_MEASURES:
            response = self.post({"zip": "02138", "measure_name": measure})
            self.assertIn(response.status_code, {200, 404})


if __name__ == "__main__":
    unittest.main()

