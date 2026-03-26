"""
Wallet service: balance checks, debits, credits, and transaction records.
All balance mutations use SELECT FOR UPDATE to prevent race conditions.
"""
import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transaction import Transaction, TransactionType
from app.models.wallet import Wallet
from app.utils.time import utcnow


async def get_wallet(db: AsyncSession, user_id: uuid.UUID) -> Wallet | None:
    result = await db.execute(select(Wallet).where(Wallet.user_id == user_id))
    return result.scalar_one_or_none()


async def get_balance(db: AsyncSession, user_id: uuid.UUID) -> float:
    wallet = await get_wallet(db, user_id)
    return float(wallet.balance) if wallet else 0.0


async def debit_wallet(
    db: AsyncSession,
    user_id: uuid.UUID,
    amount: float,
    reference_type: str | None = None,
    reference_id: str | None = None,
    description: str | None = None,
) -> Wallet:
    """
    Deduct `amount` from the wallet.
    Uses SELECT FOR UPDATE to prevent concurrent overdrafts.
    Raises ValueError if balance is insufficient.
    """
    result = await db.execute(
        select(Wallet).where(Wallet.user_id == user_id).with_for_update()
    )
    wallet = result.scalar_one_or_none()
    if wallet is None:
        raise ValueError("Wallet not found for user")

    current = Decimal(str(wallet.balance))
    debit = Decimal(str(amount))

    if current < debit:
        raise ValueError(f"Insufficient balance: have {current}, need {debit}")

    wallet.balance = float(current - debit)
    wallet.updated_at = utcnow()

    txn = Transaction(
        user_id=user_id,
        type=TransactionType.debit,
        amount=-amount,   # negative = money leaving
        currency=wallet.currency,
        reference_type=reference_type,
        reference_id=reference_id,
        description=description,
    )
    db.add(txn)
    await db.flush()
    return wallet


async def credit_wallet(
    db: AsyncSession,
    user_id: uuid.UUID,
    amount: float,
    txn_type: TransactionType = TransactionType.topup,
    description: str | None = None,
    created_by_user_id: uuid.UUID | None = None,
) -> Wallet:
    """Add `amount` to the wallet and record a transaction."""
    result = await db.execute(
        select(Wallet).where(Wallet.user_id == user_id).with_for_update()
    )
    wallet = result.scalar_one_or_none()
    if wallet is None:
        raise ValueError("Wallet not found for user")

    wallet.balance = float(Decimal(str(wallet.balance)) + Decimal(str(amount)))
    wallet.updated_at = utcnow()

    txn = Transaction(
        user_id=user_id,
        type=txn_type,
        amount=amount,
        currency=wallet.currency,
        description=description,
        created_by_user_id=created_by_user_id,
    )
    db.add(txn)
    await db.flush()
    return wallet


async def list_transactions(
    db: AsyncSession, user_id: uuid.UUID, limit: int = 50, offset: int = 0
) -> list[Transaction]:
    result = await db.execute(
        select(Transaction)
        .where(Transaction.user_id == user_id)
        .order_by(Transaction.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all())
