"""
API key service: create, list, revoke, and validate API keys.

Security model:
  - Full key is returned ONCE at creation.
  - We store only: prefix (first 20 chars) + bcrypt hash of full key.
  - Validation: hash the incoming key, compare with stored hash.
"""
import uuid
from datetime import datetime, timezone

from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.api_key import ApiKey, ApiKeyStatus
from app.models.user import User
from app.schemas.api_key import ApiKeyCreateRequest
from app.utils.idgen import generate_api_key, extract_key_prefix

# Separate CryptContext for API keys — bcrypt is fine here too.
key_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def create_api_key(db: AsyncSession, user: User, data: ApiKeyCreateRequest) -> tuple[ApiKey, str]:
    """
    Generate a new API key.
    Returns (ApiKey ORM object, plaintext_key).
    The plaintext key must be shown to the user exactly once.
    """
    plaintext = generate_api_key()
    prefix = extract_key_prefix(plaintext)
    hashed = key_context.hash(plaintext)

    key = ApiKey(
        user_id=user.id,
        name=data.name,
        key_prefix=prefix,
        key_hash=hashed,
        expires_at=data.expires_at,
    )
    db.add(key)
    await db.flush()
    return key, plaintext


async def list_api_keys(db: AsyncSession, user_id: uuid.UUID) -> list[ApiKey]:
    result = await db.execute(
        select(ApiKey)
        .where(ApiKey.user_id == user_id, ApiKey.status == ApiKeyStatus.active)
        .order_by(ApiKey.created_at.desc())
    )
    return list(result.scalars().all())


async def revoke_api_key(db: AsyncSession, key_id: uuid.UUID, user_id: uuid.UUID) -> bool:
    """Revoke a key owned by user_id. Returns False if not found."""
    result = await db.execute(
        select(ApiKey).where(ApiKey.id == key_id, ApiKey.user_id == user_id)
    )
    key = result.scalar_one_or_none()
    if key is None:
        return False
    key.status = ApiKeyStatus.revoked
    await db.flush()
    return True


async def validate_api_key(db: AsyncSession, plaintext: str) -> ApiKey | None:
    """
    Find and validate an API key from a plaintext bearer token.
    Returns the ApiKey row on success, None on failure.

    Strategy: extract the prefix, fetch all non-revoked keys with that prefix,
    then bcrypt-verify each (typically just one) to find the match.
    """
    prefix = extract_key_prefix(plaintext)
    result = await db.execute(
        select(ApiKey).where(
            ApiKey.key_prefix == prefix,
            ApiKey.status == ApiKeyStatus.active,
        )
    )
    candidates = result.scalars().all()

    for candidate in candidates:
        # Check expiry
        if candidate.expires_at and candidate.expires_at < datetime.now(timezone.utc):
            continue
        if key_context.verify(plaintext, candidate.key_hash):
            # Update last_used_at without blocking the caller
            candidate.last_used_at = datetime.now(timezone.utc)
            await db.flush()
            return candidate

    return None
