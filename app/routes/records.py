from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_roles
from app.db import get_db
from app.models.record import RecordType
from app.models.user import User, UserRole
from app.schemas.record_schema import RecordCreate, RecordListResponse, RecordResponse, RecordUpdate
from app.services.record_service import (
    create_record,
    get_record_by_id,
    list_records,
    soft_delete_record,
    update_record,
)

router = APIRouter(prefix="/records", tags=["Financial Records"])

_admin_only = require_roles(UserRole.admin)


@router.post("/", response_model=RecordResponse, status_code=status.HTTP_201_CREATED)
def create_financial_record(
    payload: RecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(_admin_only),
):
    """Admin: Create a new financial record."""
    return create_record(db, payload, user_id=current_user.id)


@router.get("/", response_model=RecordListResponse)
def get_records(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    record_type: Optional[RecordType] = Query(None, alias="type"),
    category: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    search: Optional[str] = Query(None, min_length=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """All roles: List records with optional filtering and pagination."""
    records, total = list_records(
        db,
        page=page,
        page_size=page_size,
        record_type=record_type,
        category=category,
        start_date=start_date,
        end_date=end_date,
        search=search,
    )
    return RecordListResponse(total=total, page=page, page_size=page_size, records=records)


@router.get("/{record_id}", response_model=RecordResponse)
def get_record(
    record_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """All roles: Get a single record by ID."""
    return get_record_by_id(db, record_id)


@router.put("/{record_id}", response_model=RecordResponse)
def update_financial_record(
    record_id: int,
    payload: RecordUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(_admin_only),
):
    """Admin: Update a financial record."""
    return update_record(db, record_id, payload)


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_financial_record(
    record_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(_admin_only),
):
    """Admin: Soft-delete a financial record."""
    soft_delete_record(db, record_id)
