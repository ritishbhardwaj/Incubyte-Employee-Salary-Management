import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class CompensationCreate(BaseModel):
    annual_salary: Decimal = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3)
    effective_from: date | None = None
    reason: str = Field(min_length=1, max_length=500)


class CompensationAdjust(BaseModel):
    annual_salary: Decimal = Field(gt=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    effective_from: date | None = None
    reason: str = Field(min_length=1, max_length=500)


class CompensationOut(BaseModel):
    id: uuid.UUID
    employee_id: uuid.UUID
    annual_salary: Decimal
    currency: str
    fx_rate_to_usd: Decimal
    annual_salary_usd: Decimal
    effective_from: date
    effective_to: date | None
    reason: str
    created_at: datetime
    created_by: uuid.UUID

    model_config = {"from_attributes": True}
