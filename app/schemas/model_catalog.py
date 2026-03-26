"""Pydantic schemas for the model catalog."""
import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.model_catalog import ModelModality, ModelProvider


class ModelOut(BaseModel):
    id: uuid.UUID
    public_name: str
    provider: ModelProvider
    modality: ModelModality
    input_price_per_1k: float
    output_price_per_1k: float

    model_config = {"from_attributes": True}


class ModelCreateRequest(BaseModel):
    public_name: str
    provider: ModelProvider
    upstream_model: str
    modality: ModelModality = ModelModality.text
    input_price_per_1k: float
    output_price_per_1k: float
    enabled: bool = True
    is_public: bool = True


class ModelUpdateRequest(BaseModel):
    input_price_per_1k: float | None = None
    output_price_per_1k: float | None = None
    enabled: bool | None = None
    is_public: bool | None = None


class ModelAdminOut(BaseModel):
    id: uuid.UUID
    public_name: str
    provider: ModelProvider
    upstream_model: str
    modality: ModelModality
    input_price_per_1k: float
    output_price_per_1k: float
    enabled: bool
    is_public: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
