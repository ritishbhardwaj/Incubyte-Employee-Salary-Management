"""PostgreSQL-only percentile query.

SQLite tests must not pretend this dialect path runs. Callers check the bind
dialect before importing/using this module's SQL.
"""

from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.orm import Session


def percentile_cont_usd(db: Session, usd_subquery_sql: str) -> dict[str, Decimal | None]:
    """usd_subquery_sql must be a SELECT returning a single numeric column named usd."""
    sql = text(
        f"""
        SELECT
            percentile_cont(0.25) WITHIN GROUP (ORDER BY usd) AS p25,
            percentile_cont(0.50) WITHIN GROUP (ORDER BY usd) AS p50,
            percentile_cont(0.75) WITHIN GROUP (ORDER BY usd) AS p75,
            percentile_cont(0.90) WITHIN GROUP (ORDER BY usd) AS p90
        FROM ({usd_subquery_sql}) AS pay
        """
    )
    row = db.execute(sql).one()

    def _dec(value: object) -> Decimal | None:
        if value is None:
            return None
        return Decimal(str(value))

    return {
        "p25": _dec(row.p25),
        "p50": _dec(row.p50),
        "p75": _dec(row.p75),
        "p90": _dec(row.p90),
    }
