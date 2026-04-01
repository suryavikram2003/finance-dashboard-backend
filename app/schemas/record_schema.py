from datetime import date as date_type
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.models.record import RecordType


class RecordCreate(BaseModel):
    amount: float = Field(..., gt=0, description="Amount must be positive")
    record_type: RecordType = Field(..., alias="type")
    category: str = Field(..., min_length=1, max_length=100)
    record_date: date_type = Field(default_factory=date_type.today, alias="date")
    notes: Optional[str] = Field(None, max_length=1000)

    model_config = {"populate_by_name": True}

    @field_validator("category")
    @classmethod
    def category_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Category cannot be blank")
        return v.strip()


class RecordUpdate(BaseModel):
    amount: Optional[float] = Field(None, gt=0)
    record_type: Optional[RecordType] = Field(None, alias="type")
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    record_date: Optional[date_type] = Field(None, alias="date")
    notes: Optional[str] = Field(None, max_length=1000)

    model_config = {"populate_by_name": True}

    @field_validator("category")
    @classmethod
    def category_not_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Category cannot be blank")
        return v.strip() if v else v


class RecordResponse(BaseModel):
    id: int
    user_id: int
    amount: float
    type: RecordType
    category: str
    date: date_type
    notes: Optional[str]
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RecordListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    records: list[RecordResponse]
