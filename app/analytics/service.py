from decimal import Decimal

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.compensation.models import CompensationRecord
from app.employees.models import Employee, EmploymentStatus

USD_BUCKETS = (
    (Decimal("0"), Decimal("40000"), "0-40k"),
    (Decimal("40000"), Decimal("60000"), "40-60k"),
    (Decimal("60000"), Decimal("80000"), "60-80k"),
    (Decimal("80000"), Decimal("100000"), "80-100k"),
    (Decimal("100000"), Decimal("130000"), "100-130k"),
    (Decimal("130000"), Decimal("160000"), "130-160k"),
    (Decimal("160000"), Decimal("200000"), "160-200k"),
    (Decimal("200000"), None, "200k+"),
)

SEED_REASON = "Seed"


def _current_active():
    return (
        select(
            CompensationRecord.annual_salary_usd.label("usd"),
            Employee.country.label("country"),
            Employee.department.label("department"),
            Employee.job_level.label("job_level"),
        )
        .join(Employee, Employee.id == CompensationRecord.employee_id)
        .where(
            Employee.employment_status == EmploymentStatus.ACTIVE.value,
            CompensationRecord.effective_to.is_(None),
        )
    )


def _zero() -> Decimal:
    return Decimal("0.00")


def summary(db: Session) -> dict:
    sub = _current_active().subquery()
    row = db.execute(
        select(
            func.count().label("headcount"),
            func.coalesce(func.sum(sub.c.usd), 0).label("total"),
            func.avg(sub.c.usd).label("average"),
        )
    ).one()
    headcount = int(row.headcount or 0)
    total = Decimal(str(row.total or 0)).quantize(Decimal("0.01"))
    average = (
        Decimal(str(row.average)).quantize(Decimal("0.01")) if row.average is not None else None
    )
    percentiles = _percentiles(db)
    return {
        "active_headcount": headcount,
        "total_annual_payroll_usd": total,
        "average_salary_usd": average,
        "median_salary_usd": percentiles["p50"],
        "percentiles": percentiles,
    }


def _percentiles(db: Session) -> dict:
    dialect = db.get_bind().dialect.name
    empty = {
        "p25": None,
        "p50": None,
        "p75": None,
        "p90": None,
        "dialect": dialect,
        "source": "unavailable",
    }
    if dialect != "postgresql":
        # Intentionally not computed in Python so SQLite tests cannot hide the
        # production PostgreSQL percentile_cont path. See Docs/TRADEOFFS.md.
        return {**empty, "source": "postgresql_percentile_cont_only"}
    from app.analytics.pg_percentiles import percentile_cont_usd

    sql = """
        SELECT cr.annual_salary_usd AS usd
        FROM compensation_records cr
        JOIN employees e ON e.id = cr.employee_id
        WHERE e.employment_status = 'ACTIVE' AND cr.effective_to IS NULL
    """
    values = percentile_cont_usd(db, sql)
    return {**values, "dialect": dialect, "source": "percentile_cont"}


def breakdowns(db: Session) -> dict:
    return {
        "country": _group(db, "country"),
        "department": _group(db, "department"),
        "job_level": _group(db, "job_level"),
    }


def _group(db: Session, field: str) -> list[dict]:
    sub = _current_active().subquery()
    column = getattr(sub.c, field)
    rows = db.execute(
        select(
            column.label("key"),
            func.count().label("headcount"),
            func.coalesce(func.sum(sub.c.usd), 0).label("total"),
            func.avg(sub.c.usd).label("average"),
        )
        .group_by(column)
        .order_by(column)
    ).all()
    result = []
    for row in rows:
        average = (
            Decimal(str(row.average)).quantize(Decimal("0.01")) if row.average is not None else None
        )
        result.append(
            {
                "key": row.key,
                "headcount": int(row.headcount),
                "total_usd": Decimal(str(row.total)).quantize(Decimal("0.01")),
                "average_usd": average,
            }
        )
    return result


def distribution(db: Session) -> list[dict]:
    sub = _current_active().subquery()
    bucket_expr = case(
        *[
            (
                (sub.c.usd >= low) if high is None else ((sub.c.usd >= low) & (sub.c.usd < high)),
                label,
            )
            for low, high, label in USD_BUCKETS
        ],
        else_="other",
    )
    rows = {
        row.label: int(row.headcount)
        for row in db.execute(
            select(bucket_expr.label("label"), func.count().label("headcount")).group_by(
                bucket_expr
            )
        ).all()
    }
    return [
        {
            "label": label,
            "min_usd": low,
            "max_usd": high,
            "headcount": rows.get(label, 0),
        }
        for low, high, label in USD_BUCKETS
    ]


def recent_changes(db: Session, *, limit: int = 20) -> list[dict]:
    stmt = (
        select(CompensationRecord, Employee)
        .join(Employee, Employee.id == CompensationRecord.employee_id)
        .where(CompensationRecord.reason != SEED_REASON)
        .order_by(CompensationRecord.created_at.desc())
        .limit(limit)
    )
    items = []
    for record, employee in db.execute(stmt).all():
        items.append(
            {
                "id": record.id,
                "employee_id": employee.id,
                "employee_code": employee.employee_code,
                "employee_name": f"{employee.first_name} {employee.last_name}",
                "annual_salary": record.annual_salary,
                "currency": record.currency,
                "annual_salary_usd": record.annual_salary_usd,
                "reason": record.reason,
                "effective_from": record.effective_from,
                "created_at": record.created_at,
            }
        )
    return items
