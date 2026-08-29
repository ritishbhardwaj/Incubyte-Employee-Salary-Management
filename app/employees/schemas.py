import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field

from app.compensation.schemas import CompensationCreate, CompensationOut
from app.employees.models import EmploymentStatus


class EmployeeCreate(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    country: str = Field(min_length=1, max_length=100)
    city: str = Field(min_length=1, max_length=100)
    department: str = Field(min_length=1, max_length=100)
    job_title: str = Field(min_length=1, max_length=150)
    job_level: str = Field(min_length=1, max_length=16)
    employment_status: EmploymentStatus = EmploymentStatus.ACTIVE
    hire_date: date
    employee_code: str | None = Field(default=None, max_length=32)
    compensation: CompensationCreate


class EmployeePatch(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    email: EmailStr | None = None
    country: str | None = Field(default=None, min_length=1, max_length=100)
    city: str | None = Field(default=None, min_length=1, max_length=100)
    department: str | None = Field(default=None, min_length=1, max_length=100)
    job_title: str | None = Field(default=None, min_length=1, max_length=150)
    job_level: str | None = Field(default=None, min_length=1, max_length=16)
    employment_status: EmploymentStatus | None = None
    hire_date: date | None = None


class CurrentCompensationOut(BaseModel):
    annual_salary: Decimal
    currency: str
    fx_rate_to_usd: Decimal
    annual_salary_usd: Decimal
    effective_from: date
    reason: str


class EmployeeListItem(BaseModel):
    id: uuid.UUID
    employee_code: str
    first_name: str
    last_name: str
    email: EmailStr
    country: str
    city: str
    department: str
    job_title: str
    job_level: str
    employment_status: str
    hire_date: date
    current_compensation: CurrentCompensationOut | None = None


class EmployeeDetail(EmployeeListItem):
    created_at: datetime
    updated_at: datetime
    compensation_history: list[CompensationOut] = []


class EmployeeListResponse(BaseModel):
    items: list[EmployeeListItem]
    total: int
    page: int
    page_size: int


class FilterOptions(BaseModel):
    countries: list[str]
    departments: list[str]
    job_levels: list[str]
    statuses: list[str]
