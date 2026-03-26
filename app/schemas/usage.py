"""Pydantic schemas for usage logs."""
import uuid
from datetime import datetime

from pydantic import BaseModel


class UsageLogOut(BaseModel):
    id: uuid.UUID
    request_id: str
    model_name: str
    provider: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_input: float
    cost_output: float
    total_cost: float
    latency_ms: int | None
    status_code: int
    success: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UsageLogAdminOut(UsageLogOut):
    user_id: uuid.UUID
    api_key_id: uuid.UUID
    upstream_model: str
    client_ip: str | None
    error_message: str | None
