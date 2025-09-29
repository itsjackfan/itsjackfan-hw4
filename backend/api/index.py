"""Flask application providing county health rankings endpoints."""

import json
import sqlite3
from pathlib import Path
from typing import List

from flask import Flask, jsonify, render_template, request
from pydantic import ValidationError

from backend.models.county_data import CountyDataRequest, CountyHealthRecord


def _templates_path() -> Path:
    return Path(__file__).parent / "templates"


app = Flask(__name__, template_folder=str(_templates_path()))
app.config.setdefault("DATABASE_PATH", Path("data.db"))


def get_database_path() -> Path:
    return Path(app.config["DATABASE_PATH"])


@app.route("/")
def root() -> str:
    return render_template("index.html")


@app.route("/health")
def health_check():
    return jsonify({"status": "healthy"})


def query_county_data(db_path: Path, payload: CountyDataRequest) -> List[dict]:
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row

    query = """
        SELECT
            chr.State AS state,
            chr.County AS county,
            chr.State_code AS state_code,
            chr.County_code AS county_code,
            chr.Year_span AS year_span,
            chr.Measure_name AS measure_name,
            chr.Measure_id AS measure_id,
            chr.Numerator AS numerator,
            chr.Denominator AS denominator,
            chr.Raw_value AS raw_value,
            chr.Confidence_Interval_Lower_Bound AS confidence_interval_lower_bound,
            chr.Confidence_Interval_Upper_Bound AS confidence_interval_upper_bound,
            chr.Data_Release_Year AS data_release_year,
            chr.fipscode AS fipscode
        FROM county_health_rankings chr
        JOIN zip_county zc ON chr.County = zc.county AND chr.State = zc.state_abbreviation
        WHERE zc.zip = ? AND chr.Measure_name = ?
        ORDER BY chr.Year_span
    """

    try:
        cursor = connection.execute(query, (payload.zip, payload.measure_name))
        rows = cursor.fetchall()
    finally:
        connection.close()

    return [CountyHealthRecord(**dict(row)).model_dump() for row in rows]


@app.route("/county_data", methods=["POST"])
def county_data_endpoint():
    try:
        data = request.get_json(force=True)
    except (TypeError, ValueError, json.JSONDecodeError):
        return jsonify(detail="Invalid JSON payload"), 422

    try:
        body = CountyDataRequest(**data)
    except ValidationError as exc:
        message = exc.errors()[0]["msg"] if exc.errors() else "Invalid request"
        if message.startswith("Value error, "):
            message = message[len("Value error, ") :]
        return jsonify(detail=message), 400

    if body.coffee == "teapot":
        return jsonify(detail="I'm a teapot"), 418

    if not body.zip:
        return jsonify(detail="Missing required field: zip"), 400

    if not body.measure_name:
        return jsonify(detail="Missing required field: measure_name"), 400

    results = query_county_data(get_database_path(), body)

    if not results:
        return jsonify(detail="No data found for provided zip and measure"), 404

    return jsonify(results)


@app.errorhandler(ValueError)
def handle_value_error(exc: ValueError):
    return jsonify(detail=str(exc)), 400


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)