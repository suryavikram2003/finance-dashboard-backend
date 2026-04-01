from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_roles
from app.db import get_db
from app.models.user import User, UserRole
from app.schemas.dashboard_schema import (
    CategoryBreakdownResponse,
    MonthlyTrendsResponse,
    RecentActivityResponse,
    SummaryResponse,
)
from app.services.dashboard_service import (
    get_category_breakdown,
    get_monthly_trends,
    get_recent_activity,
    get_summary,
)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

_analyst_or_admin = require_roles(UserRole.analyst, UserRole.admin)


@router.get("/summary", response_model=SummaryResponse)
def dashboard_summary(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """All roles: Total income, expenses, net balance, and record count."""
    return get_summary(db)


@router.get("/category-breakdown", response_model=CategoryBreakdownResponse)
def category_breakdown(
    db: Session = Depends(get_db),
    _: User = Depends(_analyst_or_admin),
):
    """Analyst + Admin: Category-wise income and expense totals."""
    return get_category_breakdown(db)


@router.get("/monthly-trends", response_model=MonthlyTrendsResponse)
def monthly_trends(
    months: int = Query(12, ge=1, le=60, description="Number of past months to include"),
    db: Session = Depends(get_db),
    _: User = Depends(_analyst_or_admin),
):
    """Analyst + Admin: Monthly income/expense trends."""
    return get_monthly_trends(db, months=months)


@router.get("/recent-activity", response_model=RecentActivityResponse)
def recent_activity(
    limit: int = Query(10, ge=1, le=50, description="Number of recent transactions"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """All roles: Most recent financial transactions."""
    return get_recent_activity(db, limit=limit)
