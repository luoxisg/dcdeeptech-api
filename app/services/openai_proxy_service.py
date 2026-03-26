"""
OpenAI proxy service — the heart of the gateway.

Flow for each request:
  1. Validate API key → get user
  2. Validate model exists in catalog and is enabled
  3. Check wallet balance ≥ estimated cost
  4. Forward to upstream via the correct provider adapter
  5. Extract usage tokens from upstream response
  6. Calculate actual cost
  7. Debit wallet
  8. Insert usage_log row
  9. Return normalized OpenAI-compatible response
"""
import time
import uuid
from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.api_key import ApiKey
from app.models.model_catalog import ModelCatalog
from app.models.user import User, UserStatus
from app.schemas.chat import ChatCompletionRequest
from app.services.api_key_service import validate_api_key
from app.services.pricing_service import calculate_cost
from app.services.provider_router import get_adapter
from app.services.usage_service import UsageRecord, insert_usage_log
from app.services.wallet_service import debit_wallet, get_balance
from app.utils.idgen import new_uuid


class ProxyError(Exception):
    """Raised with an HTTP status code and message."""
    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


async def _get_model(db: AsyncSession, public_name: str) -> ModelCatalog | None:
    result = await db.execute(
        select(ModelCatalog).where(
            ModelCatalog.public_name == public_name,
            ModelCatalog.enabled == True,   # noqa: E712
        )
    )
    return result.scalar_one_or_none()


async def handle_chat_completion(
    db: AsyncSession,
    raw_api_key: str,
    request: ChatCompletionRequest,
    client_ip: str | None,
) -> dict[str, Any]:
    """
    Full proxy pipeline. Returns an OpenAI-compatible response dict.
    Raises ProxyError on any validation or upstream failure.
    """
    # ── 1. Validate API key ───────────────────────────────────────────────────
    api_key: ApiKey | None = await validate_api_key(db, raw_api_key)
    if api_key is None:
        raise ProxyError(401, "Invalid or revoked API key")

    # Inline user fetch to avoid extra query when called from proxy endpoint
    from app.services.auth_service import get_user_by_id
    user: User | None = await get_user_by_id(db, api_key.user_id)
    if user is None or user.status != UserStatus.active:
        raise ProxyError(403, "Account is not active")

    # ── 2. Validate model ─────────────────────────────────────────────────────
    model_row = await _get_model(db, request.model)
    if model_row is None:
        raise ProxyError(404, f"Model '{request.model}' not found or not available")

    # ── 3. Check wallet balance (rough pre-flight; exact debit happens after) ─
    balance = await get_balance(db, user.id)
    if balance <= 0:
        raise ProxyError(402, "Insufficient wallet balance. Please top up your account.")

    # ── 4. Forward to upstream ────────────────────────────────────────────────
    adapter = get_adapter(model_row.provider)
    payload = request.model_dump(exclude_none=True)

    start_ms = time.monotonic()
    upstream_error: str | None = None
    upstream_response: dict[str, Any] | None = None
    status_code = 200
    success = True

    try:
        upstream_response = await adapter.chat_completion(
            upstream_model=model_row.upstream_model,
            payload=payload,
        )
    except httpx.HTTPStatusError as exc:
        status_code = exc.response.status_code
        upstream_error = exc.response.text[:500]
        success = False
    except Exception as exc:
        status_code = 502
        upstream_error = str(exc)[:500]
        success = False

    latency_ms = int((time.monotonic() - start_ms) * 1000)

    # ── 5. Extract token counts ───────────────────────────────────────────────
    prompt_tokens = 0
    completion_tokens = 0
    total_tokens = 0

    if upstream_response:
        usage = upstream_response.get("usage") or {}
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        total_tokens = usage.get("total_tokens", prompt_tokens + completion_tokens)

    # ── 6. Calculate cost ─────────────────────────────────────────────────────
    cost_input, cost_output, total_cost = calculate_cost(
        input_price_per_1k=float(model_row.input_price_per_1k),
        output_price_per_1k=float(model_row.output_price_per_1k),
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
    )

    # ── 7. Debit wallet (only on success with actual token usage) ─────────────
    request_id = str(new_uuid())

    if success and total_cost > 0:
        try:
            await debit_wallet(
                db=db,
                user_id=user.id,
                amount=total_cost,
                reference_type="usage_log",
                reference_id=request_id,
                description=f"{request.model} · {total_tokens} tokens",
            )
        except ValueError as exc:
            raise ProxyError(402, str(exc))

    # ── 8. Insert usage log ───────────────────────────────────────────────────
    await insert_usage_log(
        db=db,
        record=UsageRecord(
            request_id=request_id,
            user_id=user.id,
            api_key_id=api_key.id,
            model_name=request.model,
            provider=model_row.provider.value,
            upstream_model=model_row.upstream_model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cost_input=cost_input,
            cost_output=cost_output,
            total_cost=total_cost,
            latency_ms=latency_ms,
            status_code=status_code,
            success=success,
            client_ip=client_ip,
            error_message=upstream_error,
        ),
    )

    # ── 9. Return response or raise upstream error ────────────────────────────
    if not success:
        raise ProxyError(status_code, upstream_error or "Upstream provider error")

    return upstream_response  # type: ignore[return-value]
