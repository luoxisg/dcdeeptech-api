"""
OpenRouter adapter — forwards requests to https://openrouter.ai/api/v1.
Returns an OpenAI-compatible response dict.
"""
from typing import Any

import httpx

from app.adapters.base import BaseAdapter
from app.core.config import settings


class OpenRouterAdapter(BaseAdapter):
    """
    Uses httpx async client to call OpenRouter.
    OpenRouter's API is fully OpenAI-compatible, so we can forward
    almost verbatim and return the upstream response directly.
    """

    def __init__(self) -> None:
        self._base_url = settings.openrouter_base_url.rstrip("/")
        self._api_key = settings.openrouter_api_key

    async def chat_completion(
        self,
        upstream_model: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Forward the chat completion to OpenRouter.
        We override the `model` field with the upstream_model identifier.
        """
        forwarded_payload = {**payload, "model": upstream_model}

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            # OpenRouter recommends these for routing/analytics
            "HTTP-Referer": "https://api.dcdeeptech.com",
            "X-Title": "DCDeepTech API Gateway",
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self._base_url}/chat/completions",
                json=forwarded_payload,
                headers=headers,
            )
            response.raise_for_status()
            return response.json()
