"""ORM model: model_catalog table."""
import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ModelProvider(str, enum.Enum):
    openrouter = "openrouter"
    vllm = "vllm"
    dahua = "dahua"
    custom = "custom"


class ModelModality(str, enum.Enum):
    text = "text"
    vision = "vision"


class ModelCatalog(Base):
    __tablename__ = "model_catalog"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    public_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    provider: Mapped[ModelProvider] = mapped_column(Enum(ModelProvider), nullable=False)
    upstream_model: Mapped[str] = mapped_column(String(200), nullable=False)
    modality: Mapped[ModelModality] = mapped_column(Enum(ModelModality), default=ModelModality.text, nullable=False)
    # Price per 1,000 tokens in USD
    input_price_per_1k: Mapped[float] = mapped_column(Numeric(10, 6), nullable=False, default=0.0)
    output_price_per_1k: Mapped[float] = mapped_column(Numeric(10, 6), nullable=False, default=0.0)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
