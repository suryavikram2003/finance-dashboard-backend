from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_roles
from app.db import get_db
from app.models.user import User, UserRole
from app.schemas.user_schema import (
    UserCreate,
    UserListResponse,
    UserPasswordChange,
    UserResponse,
    UserUpdate,
)
from app.services.user_service import (
    change_password,
    create_user,
    delete_user,
    get_user_by_id,
    list_users,
    update_user,
)
from app.utils.exceptions import ForbiddenException

router = APIRouter(prefix="/users", tags=["Users"])

_admin_only = require_roles(UserRole.admin)


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_new_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    _: User = Depends(_admin_only),
):
    """Admin: Create a new user with any role."""
    return create_user(db, payload)


@router.get("/", response_model=UserListResponse)
def get_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    role: Optional[UserRole] = Query(None),
    is_active: Optional[bool] = Query(None),
    search: Optional[str] = Query(None, min_length=1),
    db: Session = Depends(get_db),
    _: User = Depends(_admin_only),
):
    """Admin: List all users with optional filtering and pagination."""
    users, total = list_users(db, page=page, page_size=page_size, role=role, is_active=is_active, search=search)
    return UserListResponse(total=total, page=page, page_size=page_size, users=users)


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Any authenticated user: Get own profile."""
    return current_user


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Admin: Get any user. Others: Only own profile."""
    if current_user.role != UserRole.admin and current_user.id != user_id:
        raise ForbiddenException("You can only view your own profile")
    return get_user_by_id(db, user_id)


@router.patch("/{user_id}", response_model=UserResponse)
def update_user_info(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Admin: Update any user. Others: Update own profile (cannot change role)."""
    if current_user.role != UserRole.admin:
        if current_user.id != user_id:
            raise ForbiddenException("You can only update your own profile")
        if payload.role is not None:
            raise ForbiddenException("Only admins can change roles")
        if payload.is_active is not None:
            raise ForbiddenException("Only admins can change account status")
    return update_user(db, user_id, payload)


@router.post("/{user_id}/change-password", response_model=UserResponse)
def update_password(
    user_id: int,
    payload: UserPasswordChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Change own password (requires current password)."""
    if current_user.id != user_id:
        raise ForbiddenException("You can only change your own password")
    return change_password(db, current_user, payload.current_password, payload.new_password)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(_admin_only),
):
    """Admin: Permanently delete a user."""
    if current_user.id == user_id:
        raise ForbiddenException("Admins cannot delete their own account")
    delete_user(db, user_id)
