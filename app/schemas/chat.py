"""
Pydantic schemas mirroring OpenAI's chat completion API surface.
We accept the same request shape and return the same response shape
so existing OpenAI SDK clients work without modification.
"""
from typing import Any, Literal

from pydantic import BaseModel, Field


# ── Request ───────────────────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: str | list[Any]   # list[Any] allows vision/multimodal content blocks
    name: str | None = None


class ChatCompletionRequest(BaseModel):
    model: str
    messages: list[ChatMessage]
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    top_p: float | None = Field(default=None, ge=0.0, le=1.0)
    max_tokens: int | None = Field(default=None, ge=1)
    stream: bool = False
    stop: list[str] | str | None = None
    presence_penalty: float | None = None
    frequency_penalty: float | None = None
    user: str | None = None
    # Allow extra fields so we can forward them upstream without breaking validation
    model_config = {"extra": "allow"}


# ── Response ──────────────────────────────────────────────────────────────────

class UsageInfo(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChoiceMessage(BaseModel):
    role: str
    content: str | None


class Choice(BaseModel):
    index: int
    message: ChoiceMessage
    finish_reason: str | None


class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: list[Choice]
    usage: UsageInfo
