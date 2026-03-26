"""
Auth service: user registration, login, lookup.
All DB mutations go through here so routers stay thin.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.models.user import User, UserStatus
from app.models.wallet import Wallet
from app.schemas.auth import RegisterRequest
from app.core.config import settings


async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email.lower()))
    return result.scalar_one_or_none()


async def register_user(db: AsyncSession, data: RegisterRequest) -> User:
    """
    Create a new user and provision an empty wallet.
    Raises ValueError if the email is already taken.
    """
    existing = await get_user_by_email(db, data.email)
    if existing:
        raise ValueError("Email already registered")

    user = User(
        email=data.email.lower(),
        password_hash=hash_password(data.password),
        full_name=data.full_name,
        company_name=data.company_name,
        country=data.country,
    )
    db.add(user)
    await db.flush()  # populate user.id before creating wallet

    wallet = Wallet(
        user_id=user.id,
        balance=0.0,
        currency=settings.default_currency,
    )
    db.add(wallet)
    await db.flush()

    return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    """
    Verify credentials. Updates last_login_at on success.
    Returns None if credentials are wrong or account is not active.
    """
    user = await get_user_by_email(db, email)
    if user is None:
        return None
    if not verify_password(password, user.password_hash):
        return None
    if user.status != UserStatus.active:
        return None

    user.last_login_at = datetime.now(timezone.utc)
    await db.flush()
    return user
