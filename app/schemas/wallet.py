"""Pydantic schemas for wallet and transactions."""
import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.transaction import TransactionType


class WalletOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    balance: float
    currency: str
    updated_at: datetime

    model_config = {"from_attributes": True}


class TransactionOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    type: TransactionType
    amount: float
    currency: str
    reference_type: str | None
    reference_id: str | None
    description: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class WalletAdjustRequest(BaseModel):
    amount: float = Field(description="Positive for topup/credit, negative for debit/manual reduction")
    type: TransactionType = TransactionType.manual_adjustment
    description: str | None = None
