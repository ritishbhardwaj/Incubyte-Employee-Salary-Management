from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.api.schemas.analytics import BreakdownsOut, DistributionBucket, RecentChange, SummaryOut
from app.database.models import User
from app.database.session import get_db
from app.services.analytics import breakdowns, distribution, recent_changes, summary

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


@router.get("/summary", response_model=SummaryOut)
def summary_endpoint(
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    return summary(db)


@router.get("/breakdowns", response_model=BreakdownsOut)
def breakdowns_endpoint(
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    return breakdowns(db)


@router.get("/distribution", response_model=list[DistributionBucket])
def distribution_endpoint(
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> list:
    return distribution(db)


@router.get("/recent-changes", response_model=list[RecentChange])
def recent_changes_endpoint(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> list:
    return recent_changes(db, limit=limit)
