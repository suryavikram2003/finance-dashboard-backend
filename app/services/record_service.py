from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

from app.models.record import FinancialRecord, RecordType
from app.schemas.record_schema import RecordCreate, RecordUpdate
from app.utils.exceptions import NotFoundException


def create_record(db: Session, payload: RecordCreate, user_id: int) -> FinancialRecord:
    record = FinancialRecord(
        user_id=user_id,
        amount=payload.amount,
        type=payload.record_type,
        category=payload.category,
        date=payload.record_date,
        notes=payload.notes,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_record_by_id(db: Session, record_id: int) -> FinancialRecord:
    record = (
        db.query(FinancialRecord)
        .filter(FinancialRecord.id == record_id, FinancialRecord.is_deleted.is_(False))
        .first()
    )
    if not record:
        raise NotFoundException(f"Record with id {record_id} not found")
    return record


def list_records(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    record_type: Optional[RecordType] = None,
    category: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    search: Optional[str] = None,
    user_id: Optional[int] = None,
) -> tuple[list[FinancialRecord], int]:
    query = db.query(FinancialRecord).filter(FinancialRecord.is_deleted.is_(False))

    if user_id is not None:
        query = query.filter(FinancialRecord.user_id == user_id)
    if record_type is not None:
        query = query.filter(FinancialRecord.type == record_type)
    if category:
        query = query.filter(FinancialRecord.category.ilike(f"%{category}%"))
    if start_date:
        query = query.filter(FinancialRecord.date >= start_date)
    if end_date:
        query = query.filter(FinancialRecord.date <= end_date)
    if search:
        pattern = f"%{search}%"
        query = query.filter(
            (FinancialRecord.category.ilike(pattern)) | (FinancialRecord.notes.ilike(pattern))
        )

    total = query.count()
    records = (
        query.order_by(FinancialRecord.date.desc(), FinancialRecord.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return records, total


def update_record(db: Session, record_id: int, payload: RecordUpdate) -> FinancialRecord:
    record = get_record_by_id(db, record_id)

    if payload.amount is not None:
        record.amount = payload.amount
    if payload.record_type is not None:
        record.type = payload.record_type
    if payload.category is not None:
        record.category = payload.category
    if payload.record_date is not None:
        record.date = payload.record_date
    if payload.notes is not None:
        record.notes = payload.notes

    db.commit()
    db.refresh(record)
    return record


def soft_delete_record(db: Session, record_id: int) -> None:
    record = get_record_by_id(db, record_id)
    record.is_deleted = True
    db.commit()


def hard_delete_record(db: Session, record_id: int) -> None:
    record = get_record_by_id(db, record_id)
    db.delete(record)
    db.commit()
