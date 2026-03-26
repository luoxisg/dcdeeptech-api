"""
Usage service: insert usage log rows, query usage history.
"""
import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.usage_log import UsageLog


@dataclass
class UsageRecord:
    request_id: str
    user_id: uuid.UUID
    api_key_id: uuid.UUID
    model_name: str
    provider: str
    upstream_model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_input: float
    cost_output: float
    total_cost: float
    latency_ms: int | None
    status_code: int
    success: bool
    client_ip: str | None
    error_message: str | None


async def insert_usage_log(db: AsyncSession, record: UsageRecord) -> UsageLog:
    log = UsageLog(
        request_id=record.request_id,
        user_id=record.user_id,
        api_key_id=record.api_key_id,
        model_name=record.model_name,
        provider=record.provider,
        upstream_model=record.upstream_model,
        prompt_tokens=record.prompt_tokens,
        completion_tokens=record.completion_tokens,
        total_tokens=record.total_tokens,
        cost_input=record.cost_input,
        cost_output=record.cost_output,
        total_cost=record.total_cost,
        latency_ms=record.latency_ms,
        status_code=record.status_code,
        success=record.success,
        client_ip=record.client_ip,
        error_message=record.error_message,
    )
    db.add(log)
    await db.flush()
    return log


async def list_usage_for_user(
    db: AsyncSession, user_id: uuid.UUID, limit: int = 50, offset: int = 0
) -> list[UsageLog]:
    result = await db.execute(
        select(UsageLog)
        .where(UsageLog.user_id == user_id)
        .order_by(UsageLog.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all())


async def list_all_usage(
    db: AsyncSession, limit: int = 100, offset: int = 0
) -> list[UsageLog]:
    result = await db.execute(
        select(UsageLog)
        .order_by(UsageLog.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all())
