"""Import every mapped class so Base.metadata is complete for Alembic and tests."""

from app.auth.models import Session, User
from app.compensation.models import CompensationRecord
from app.employees.models import Employee

__all__ = ["User", "Session", "Employee", "CompensationRecord"]
