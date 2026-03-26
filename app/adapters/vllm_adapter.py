"""
vLLM adapter — stub for future self-hosted vLLM endpoint.
vLLM exposes an OpenAI-compatible API by default, so the implementation
mirrors the OpenRouter adapter with a different base URL / auth scheme.
"""
import os
from typing import Any

import httpx

from app.adapters.base import BaseAdapter


class VLLMAdapter(BaseAdapter):
    """
    Targets a self-hosted vLLM instance.
    Set VLLM_BASE_URL in env; auth is optional (set VLLM_API_KEY if needed).
    """

    def __init__(self) -> None:
        self._base_url = os.getenv("VLLM_BASE_URL", "http://localhost:8000").rstrip("/")
        self._api_key = os.getenv("VLLM_API_KEY", "")

    async def chat_completion(
        self,
        upstream_model: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        forwarded_payload = {**payload, "model": upstream_model}

        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(
                f"{self._base_url}/v1/chat/completions",
                json=forwarded_payload,
                headers=headers,
            )
            response.raise_for_status()
            return response.json()
