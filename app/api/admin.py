"""
Admin-only router.
All endpoints here require role == "admin" (enforced via AdminUser dep).
"""
import uuid

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import AdminUser, DbDep
from app.models.model_catalog import ModelCatalog
from app.models.user import User
from app.schemas.model_catalog import ModelAdminOut, ModelCreateRequest, ModelUpdateRequest
from app.schemas.usage import UsageLogAdminOut
from app.schemas.user import UserListItem
from app.schemas.wallet import TransactionOut, WalletAdjustRequest
from app.services.usage_service import list_all_usage
from app.services.wallet_service import credit_wallet, debit_wallet
from app.models.transaction import TransactionType

router = APIRouter(prefix="/admin", tags=["Admin"])


# ── Users ─────────────────────────────────────────────────────────────────────

@router.get("/users", response_model=list[UserListItem])
async def admin_list_users(
    admin: AdminUser,
    db: DbDep,
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> list[UserListItem]:
    result = await db.execute(
        select(User).order_by(User.created_at.desc()).limit(limit).offset(offset)
    )
    users = result.scalars().all()
    return [UserListItem.model_validate(u) for u in users]


# ── Usage ─────────────────────────────────────────────────────────────────────

@router.get("/usage", response_model=list[UsageLogAdminOut])
async def admin_list_usage(
    admin: AdminUser,
    db: DbDep,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> list[UsageLogAdminOut]:
    logs = await list_all_usage(db, limit=limit, offset=offset)
    return [UsageLogAdminOut.model_validate(log) for log in logs]


# ── Wallet adjustments ────────────────────────────────────────────────────────

@router.post("/wallets/{user_id}/adjust", response_model=TransactionOut)
async def admin_adjust_wallet(
    user_id: uuid.UUID,
    body: WalletAdjustRequest,
    admin: AdminUser,
    db: DbDep,
) -> TransactionOut:
    """
    Credit or debit a user's wallet manually.
    Positive amount = credit; negative amount = debit.
    """
    try:
        if body.amount >= 0:
            wallet = await credit_wallet(
                db=db,
                user_id=user_id,
                amount=body.amount,
                txn_type=body.type,
                description=body.description,
                created_by_user_id=admin.id,
            )
        else:
            wallet = await debit_wallet(
                db=db,
                user_id=user_id,
                amount=abs(body.amount),
                description=body.description,
            )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    # Return the latest transaction for this user
    from sqlalchemy import select as sa_select
    from app.models.transaction import Transaction
    result = await db.execute(
        sa_select(Transaction)
        .where(Transaction.user_id == user_id)
        .order_by(Transaction.created_at.desc())
        .limit(1)
    )
    txn = result.scalar_one()
    return TransactionOut.model_validate(txn)


# ── Model catalog management ──────────────────────────────────────────────────

@router.post("/models", response_model=ModelAdminOut, status_code=status.HTTP_201_CREATED)
async def admin_create_model(
    body: ModelCreateRequest, admin: AdminUser, db: DbDep
) -> ModelAdminOut:
    """Add a new model to the catalog."""
    existing = await db.execute(
        select(ModelCatalog).where(ModelCatalog.public_name == body.public_name)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Model with that public_name already exists")

    model = ModelCatalog(**body.model_dump())
    db.add(model)
    await db.flush()
    return ModelAdminOut.model_validate(model)


@router.patch("/models/{model_id}", response_model=ModelAdminOut)
async def admin_update_model(
    model_id: uuid.UUID, body: ModelUpdateRequest, admin: AdminUser, db: DbDep
) -> ModelAdminOut:
    """Update pricing or availability flags for a model."""
    result = await db.execute(select(ModelCatalog).where(ModelCatalog.id == model_id))
    model = result.scalar_one_or_none()
    if model is None:
        raise HTTPException(status_code=404, detail="Model not found")

    update_data = body.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(model, field, value)

    await db.flush()
    return ModelAdminOut.model_validate(model)
