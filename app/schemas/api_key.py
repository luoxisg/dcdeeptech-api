"""Pydantic schemas for API key management."""
import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.api_key import ApiKeyStatus


class ApiKeyCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    expires_at: datetime | None = None


class ApiKeyCreatedResponse(BaseModel):
    """
    Returned ONCE at creation time — includes the full plaintext key.
    After this, only the prefix is available.
    """
    id: uuid.UUID
    name: str
    key: str          # full plaintext — shown once
    key_prefix: str
    status: ApiKeyStatus
    created_at: datetime
    expires_at: datetime | None

    model_config = {"from_attributes": True}


class ApiKeyOut(BaseModel):
    """Safe key representation — prefix only, no plaintext."""
    id: uuid.UUID
    name: str
    key_prefix: str
    status: ApiKeyStatus
    created_at: datetime
    last_used_at: datetime | None
    expires_at: datetime | None

    model_config = {"from_attributes": True}
