from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.record import FinancialRecord, RecordType
from app.schemas.dashboard_schema import (
    CategoryBreakdownResponse,
    CategoryTotal,
    MonthlyTrend,
    MonthlyTrendsResponse,
    RecentActivityResponse,
    RecentTransaction,
    SummaryResponse,
)


def get_summary(db: Session) -> SummaryResponse:
    rows = (
        db.query(FinancialRecord.type, func.sum(FinancialRecord.amount))
        .filter(FinancialRecord.is_deleted.is_(False))
        .group_by(FinancialRecord.type)
        .all()
    )

    totals = {row[0]: row[1] or 0.0 for row in rows}
    total_income = float(totals.get(RecordType.income, 0.0))
    total_expense = float(totals.get(RecordType.expense, 0.0))

    record_count = (
        db.query(func.count(FinancialRecord.id))
        .filter(FinancialRecord.is_deleted.is_(False))
        .scalar()
        or 0
    )

    return SummaryResponse(
        total_income=total_income,
        total_expense=total_expense,
        net_balance=total_income - total_expense,
        record_count=record_count,
    )


def get_category_breakdown(db: Session) -> CategoryBreakdownResponse:
    rows = (
        db.query(
            FinancialRecord.category,
            FinancialRecord.type,
            func.sum(FinancialRecord.amount),
            func.count(FinancialRecord.id),
        )
        .filter(FinancialRecord.is_deleted.is_(False))
        .group_by(FinancialRecord.category, FinancialRecord.type)
        .order_by(FinancialRecord.type, func.sum(FinancialRecord.amount).desc())
        .all()
    )

    breakdown = [
        CategoryTotal(
            category=row[0],
            type=row[1].value if hasattr(row[1], "value") else str(row[1]),
            total=float(row[2]),
            count=row[3],
        )
        for row in rows
    ]
    return CategoryBreakdownResponse(breakdown=breakdown)


def get_monthly_trends(db: Session, months: int = 12) -> MonthlyTrendsResponse:
    from sqlalchemy import extract

    rows = (
        db.query(
            extract("year", FinancialRecord.date).label("year"),
            extract("month", FinancialRecord.date).label("month"),
            FinancialRecord.type,
            func.sum(FinancialRecord.amount),
        )
        .filter(FinancialRecord.is_deleted.is_(False))
        .group_by("year", "month", FinancialRecord.type)
        .order_by("year", "month")
        .all()
    )

    monthly: dict[tuple[int, int], dict] = {}
    for year, month, rec_type, total in rows:
        key = (int(year), int(month))
        if key not in monthly:
            monthly[key] = {"income": 0.0, "expense": 0.0}
        t_val = rec_type.value if hasattr(rec_type, "value") else str(rec_type)
        monthly[key][t_val] = float(total)

    trends = [
        MonthlyTrend(
            year=k[0],
            month=k[1],
            income=v["income"],
            expense=v["expense"],
            net=v["income"] - v["expense"],
        )
        for k, v in sorted(monthly.items())
    ]

    if months:
        trends = trends[-months:]

    return MonthlyTrendsResponse(trends=trends)


def get_recent_activity(db: Session, limit: int = 10) -> RecentActivityResponse:
    records = (
        db.query(FinancialRecord)
        .filter(FinancialRecord.is_deleted.is_(False))
        .order_by(FinancialRecord.date.desc(), FinancialRecord.id.desc())
        .limit(limit)
        .all()
    )

    transactions = [
        RecentTransaction(
            id=r.id,
            amount=r.amount,
            type=r.type.value if hasattr(r.type, "value") else str(r.type),
            category=r.category,
            date=str(r.date),
            notes=r.notes,
        )
        for r in records
    ]
    return RecentActivityResponse(transactions=transactions)
