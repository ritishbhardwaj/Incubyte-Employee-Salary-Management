from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class Percentiles(BaseModel):
    p25: Decimal | None = None
    p50: Decimal | None = None
    p75: Decimal | None = None
    p90: Decimal | None = None
    dialect: str
    source: str


class SummaryOut(BaseModel):
    active_headcount: int
    total_annual_payroll_usd: Decimal
    average_salary_usd: Decimal | None
    median_salary_usd: Decimal | None
    percentiles: Percentiles


class BreakdownRow(BaseModel):
    key: str
    headcount: int
    total_usd: Decimal
    average_usd: Decimal | None


class BreakdownsOut(BaseModel):
    country: list[BreakdownRow]
    department: list[BreakdownRow]
    job_level: list[BreakdownRow]


class DistributionBucket(BaseModel):
    label: str
    min_usd: Decimal
    max_usd: Decimal | None
    headcount: int


class RecentChange(BaseModel):
    id: UUID
    employee_id: UUID
    employee_code: str
    employee_name: str
    annual_salary: Decimal
    currency: str
    annual_salary_usd: Decimal
    reason: str
    effective_from: date
    created_at: datetime
