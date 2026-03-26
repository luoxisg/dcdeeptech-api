"""Pydantic schemas for user objects."""
import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr

from app.models.user import UserRole, UserStatus


class UserOut(BaseModel):
    """Safe public representation of a user (no password hash)."""
    id: uuid.UUID
    email: EmailStr
    full_name: str | None
    role: UserRole
    status: UserStatus
    company_name: str | None
    country: str | None
    created_at: datetime
    last_login_at: datetime | None

    model_config = {"from_attributes": True}


class UserListItem(BaseModel):
    id: uuid.UUID
    email: EmailStr
    full_name: str | None
    role: UserRole
    status: UserStatus
    created_at: datetime

    model_config = {"from_attributes": True}
