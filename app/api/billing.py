"""Billing router: wallet balance and transaction history."""
from fastapi import APIRouter, Query

from app.core.deps import CurrentUser, DbDep
from app.schemas.wallet import TransactionOut, WalletOut
from app.services.wallet_service import get_wallet, list_transactions

router = APIRouter(prefix="/v1/billing", tags=["Billing"])


@router.get("/wallet", response_model=WalletOut)
async def get_wallet_endpoint(current_user: CurrentUser, db: DbDep) -> WalletOut:
    """Return the current wallet balance for the authenticated user."""
    wallet = await get_wallet(db, current_user.id)
    if wallet is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Wallet not found")
    return WalletOut.model_validate(wallet)


@router.get("/transactions", response_model=list[TransactionOut])
async def get_transactions(
    current_user: CurrentUser,
    db: DbDep,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[TransactionOut]:
    """Return paginated transaction history for the current user."""
    txns = await list_transactions(db, current_user.id, limit=limit, offset=offset)
    return [TransactionOut.model_validate(t) for t in txns]
