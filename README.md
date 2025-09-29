# itsjackfan-hw4

Backend tooling for turning County Health Rankings CSV exports into a SQLite database and serving county-level statistics via a FastAPI endpoint.

---

## Repository Layout

```
itsjackfan-hw4/
├── backend/
│   ├── api/main.py                # FastAPI application entry point
│   ├── models/county_data.py      # Pydantic models and validation logic
│   ├── scripts/                   # (placeholder for backend-specific scripts)
│   ├── tests/                     # Unit tests for CSV conversion + API
│   ├── pyproject.toml, uv.lock    # Poetry dependency metadata
├── csv_to_sqlite.py               # CLI for loading a CSV file into SQLite
├── county_health_rankings.csv     # Source data (large)
├── zip_county.csv                 # ZIP ⇄ county crosswalk (large)
├── data.db                        # Generated SQLite database (ignored by git)
└── README.md                      # This file
```

---

## Prerequisites

- Python 3.10 or newer (developed with Python 3.12 on macOS 15)
- `pip` to install dependencies
- Optional: [`jq`](https://stedolan.github.io/jq/) for pretty-printing JSON in curl tests

If you use `pyenv`, install/activate the desired Python version before creating the virtual environment.

---

## Environment Setup

1. **Create and activate a virtual environment**

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
   ```

2. **Install backend dependencies**

   The backend uses Poetry metadata. From the repository root:

   ```bash
   cd backend
   pip install \
     "fastapi>=0.118.0" \
     "uvicorn>=0.37.0"
   cd ..
   ```

   > If you prefer Poetry, you can run `poetry install` inside `backend/` instead of using `pip`.

---

## Building `data.db`

The API expects a SQLite database named `data.db` in the project root. Two CSVs are included to seed the database:

- `zip_county.csv`
- `county_health_rankings.csv`

Use the conversion script (run from the root directory). Each run creates a table named after the CSV file (characters other than letters/digits become underscores).

```bash
# Rebuild the ZIP ⇄ county lookup table
python csv_to_sqlite.py data.db zip_county.csv

# Add the County Health Rankings table
python csv_to_sqlite.py data.db county_health_rankings.csv
```

Verify the tables:

```bash
sqlite3 data.db ".tables"
# → county_health_rankings  zip_county

sqlite3 data.db "PRAGMA table_info(zip_county);"
sqlite3 data.db "PRAGMA table_info(county_health_rankings);"
```

If you rerun the converter on the same CSV, the corresponding table is dropped and recreated, ensuring a clean import.

---

## Running the FastAPI Server

From the repository root:

```bash
uvicorn backend.api.main:app --reload
```

Endpoints:

- `GET /` → `{"message": "Hello World"}`
- `GET /health` → `{"status": "healthy"}`
- `POST /county_data` → returns county health metrics filtered by ZIP and measure

---

## `/county_data` Endpoint Reference

### Request Schema

```json
{
  "zip": "02138",             // required 5-digit ZIP code
  "measure_name": "Adult obesity",  // required, must match allowed list
  "coffee": "teapot"          // optional; if set, returns HTTP 418 regardless of other fields
}
```

Allowed `measure_name` values (see `backend/models/county_data.py`):

```
Violent crime rate, Unemployment, Children in poverty, Diabetic screening,
Mammography screening, Preventable hospital stays, Uninsured,
Sexually transmitted infections, Physical inactivity, Adult obesity,
Premature Death, Daily fine particulate matter
```

### Behaviour Summary

- Missing `zip` or `measure_name` → HTTP 400 with descriptive message
- Invalid `measure_name` → HTTP 400
- `coffee="teapot"` → HTTP 418 (“I’m a teapot”), overriding other logic
- No matching rows → HTTP 404
- ZIP validation rejects injection attempts (only 5-digit numeric values allowed)

### Example Commands

```bash
# Full adult obesity dataset for ZIP 02138 (Cambridge, MA)
curl -s -X POST http://127.0.0.1:8000/county_data \
  -H "Content-Type: application/json" \
  -d '{"zip":"02138","measure_name":"Adult obesity"}' | jq

# Filter the response for the 2009 row
curl -s -X POST http://127.0.0.1:8000/county_data \
  -H "Content-Type: application/json" \
  -d '{"zip":"02138","measure_name":"Adult obesity"}' \
  | jq 'map(select(.year_span=="2009"))'

# Alternate measure name
curl -s -X POST http://127.0.0.1:8000/county_data \
  -H "Content-Type: application/json" \
  -d '{"zip":"02138","measure_name":"Unemployment"}' | jq '.'

# SQL injection guard (fails with 400)
curl -i -X POST http://127.0.0.1:8000/county_data \
  -H "Content-Type: application/json" \
  -d '{"zip":"02138'' OR ''1''=''1","measure_name":"Adult obesity"}'

# Missing field (fails with 400)
curl -i -X POST http://127.0.0.1:8000/county_data \
  -H "Content-Type: application/json" \
  -d '{"zip":"02138"}'

# Teapot easter egg (HTTP 418)
curl -i -X POST http://127.0.0.1:8000/county_data \
  -H "Content-Type: application/json" \
  -d '{"coffee":"teapot"}'
```

Typical adult obesity response (trimmed):

```json
[
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
    "fipscode": "25017"
  },
  { "year_span": "2005", "raw_value": "0.2", ... },
  { "year_span": "2010", "raw_value": "0.233", "data_release_year": "2014", ... }
]
```

---

## Running Tests

Execute both suites from the project root (tests use `unittest` and create temporary SQLite databases).

```bash
python -m unittest backend.tests.test_csv_to_sqlite backend.tests.test_county_data_endpoint
```

Coverage highlights:

- `csv_to_sqlite.py`: Header sanitisation, per-CSV table naming, re-import behaviour
- `/county_data`: Successful responses with exact payload checks, validation failures, teapot override, SQL injection attempts, and 404 handling

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
| --- | --- | --- |
| `sqlite3.OperationalError: no such table` | Database not built or wrong path | Re-run CSV conversion script(s) in repo root |
| “Field required” validation errors | CSV column names didn’t match expected casing | Regenerate tables; ensure `State`, `County`, etc. are capitalised exactly |
| HTTP 404 from `/county_data` | No data for provided ZIP/measure | Confirm ZIP exists in `zip_county` and measure exists for that county |
| Injection attempt appears to work | ZIP must be numeric; if you modify validation, keep parameterised SQL and strict checks |

---

## License

Created for coursework; no explicit open-source license is published. Contact `itsjackfan` for reuse permissions.
