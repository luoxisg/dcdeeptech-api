"""
Abstract base for upstream AI provider adapters.
Each adapter must implement `chat_completion` and return a normalized dict
that matches the OpenAI /v1/chat/completions response shape.
"""
from abc import ABC, abstractmethod
from typing import Any


class BaseAdapter(ABC):
    """
    All provider adapters inherit from this base.
    Callers only interact with the normalized interface defined here.
    """

    @abstractmethod
    async def chat_completion(
        self,
        upstream_model: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Forward a chat completion request to the upstream provider.

        Args:
            upstream_model: The provider-specific model identifier.
            payload: The full request body dict (OpenAI-shaped).

        Returns:
            A dict that is OpenAI-compatible (id, object, created, model,
            choices, usage).

        Raises:
            httpx.HTTPStatusError: on upstream 4xx/5xx responses.
        """
        ...
