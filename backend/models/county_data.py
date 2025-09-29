"""Pydantic models for the /county_data endpoint."""

from typing import List, Optional, Tuple

from pydantic import BaseModel, Field, model_validator, validator


ALLOWED_MEASURES: Tuple[str, ...] = (
    "Violent crime rate",
    "Unemployment",
    "Children in poverty",
    "Diabetic screening",
    "Mammography screening",
    "Preventable hospital stays",
    "Uninsured",
    "Sexually transmitted infections",
    "Physical inactivity",
    "Adult obesity",
    "Premature Death",
    "Daily fine particulate matter",
)


class CountyDataRequest(BaseModel):
    zip: Optional[str] = Field(None, description="5-digit ZIP code")
    measure_name: Optional[str] = Field(None, description="Name of the requested measure")
    coffee: Optional[str] = None

    @validator("zip")
    def validate_zip(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        if len(value) != 5 or not value.isdigit():
            raise ValueError("ZIP must be a 5-digit string")
        return value

    @validator("measure_name")
    def validate_measure_name(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        if value not in ALLOWED_MEASURES:
            raise ValueError("Invalid measure_name")
        return value

    @model_validator(mode="after")
    def ensure_required_fields(cls, values: "CountyDataRequest") -> "CountyDataRequest":
        if values.coffee == "teapot":
            return values

        if not values.zip:
            raise ValueError("Missing required field: zip")
        if not values.measure_name:
            raise ValueError("Missing required field: measure_name")

        return values


class CountyHealthRecord(BaseModel):
    state: str
    county: str
    state_code: str
    county_code: str
    year_span: str
    measure_name: str
    measure_id: str
    numerator: str
    denominator: str
    raw_value: str
    confidence_interval_lower_bound: str
    confidence_interval_upper_bound: str
    data_release_year: str
    fipscode: str


CountyDataResponse = List[CountyHealthRecord]

