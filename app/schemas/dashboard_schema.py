from pydantic import BaseModel


class SummaryResponse(BaseModel):
    total_income: float
    total_expense: float
    net_balance: float
    record_count: int


class CategoryTotal(BaseModel):
    category: str
    type: str
    total: float
    count: int


class CategoryBreakdownResponse(BaseModel):
    breakdown: list[CategoryTotal]


class MonthlyTrend(BaseModel):
    year: int
    month: int
    income: float
    expense: float
    net: float


class MonthlyTrendsResponse(BaseModel):
    trends: list[MonthlyTrend]


class RecentTransaction(BaseModel):
    id: int
    amount: float
    type: str
    category: str
    date: str
    notes: str | None

    model_config = {"from_attributes": True}


class RecentActivityResponse(BaseModel):
    transactions: list[RecentTransaction]
