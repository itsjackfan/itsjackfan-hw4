"""
Main API server for the backend.
Self-coded with tab autocompletion in Cursor + GPT-5-Codex.
"""

import json
import sqlite3
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
import uvicorn

from models.county_data import (
    CountyDataRequest,
    CountyDataResponse,
    CountyHealthRecord,
)


app = FastAPI()

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


def get_database_path() -> Path:
    return Path("data.db")


@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


def query_county_data(db_path: Path, payload: CountyDataRequest) -> CountyDataResponse:
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

    return [CountyHealthRecord(**dict(row)) for row in rows]


async def parse_county_data_request(request: Request) -> CountyDataRequest:
    try:
        data = await request.json()
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=422, detail="Invalid JSON payload") from exc

    try:
        return CountyDataRequest(**data)
    except ValidationError as exc:
        message = exc.errors()[0]["msg"] if exc.errors() else "Invalid request"
        if message.startswith("Value error, "):
            message = message[len("Value error, ") :]
        raise HTTPException(status_code=400, detail=message) from exc


@app.post("/county_data", response_model=CountyDataResponse)
async def county_data_endpoint(
    request: Request,
    body: CountyDataRequest = Depends(parse_county_data_request),
    db_path: Path = Depends(get_database_path),
):
    if body.coffee == "teapot":
        raise HTTPException(status_code=status.HTTP_418_IM_A_TEAPOT, detail="I'm a teapot")

    if not body.zip:
        raise HTTPException(status_code=400, detail="Missing required field: zip")

    if not body.measure_name:
        raise HTTPException(status_code=400, detail="Missing required field: measure_name")

    results = query_county_data(db_path, body)

    if not results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No data found for provided zip and measure",
        )

    return results


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(status_code=400, content={"detail": str(exc)})


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)