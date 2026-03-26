"""Public model catalog router."""
from fastapi import APIRouter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, DbDep
from app.models.model_catalog import ModelCatalog
from app.schemas.model_catalog import ModelOut

router = APIRouter(prefix="/v1/models", tags=["Models"])


@router.get("", response_model=list[ModelOut])
async def list_models(current_user: CurrentUser, db: DbDep) -> list[ModelOut]:
    """Return all enabled, public models available to authenticated users."""
    result = await db.execute(
        select(ModelCatalog)
        .where(ModelCatalog.enabled == True, ModelCatalog.is_public == True)  # noqa: E712
        .order_by(ModelCatalog.public_name)
    )
    models = result.scalars().all()
    return [ModelOut.model_validate(m) for m in models]
