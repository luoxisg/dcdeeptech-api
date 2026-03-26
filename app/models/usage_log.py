"""ORM model: usage_logs table."""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class UsageLog(Base):
    __tablename__ = "usage_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=False, index=True)
    api_key_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("api_keys.id", ondelete="SET NULL"), nullable=False)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)        # public_name used in request
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    upstream_model: Mapped[str] = mapped_column(String(200), nullable=False)    # forwarded model identifier
    prompt_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cost_input: Mapped[float] = mapped_column(Numeric(12, 8), nullable=False, default=0.0)
    cost_output: Mapped[float] = mapped_column(Numeric(12, 8), nullable=False, default=0.0)
    total_cost: Mapped[float] = mapped_column(Numeric(12, 8), nullable=False, default=0.0)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status_code: Mapped[int] = mapped_column(Integer, nullable=False, default=200)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    client_ip: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
