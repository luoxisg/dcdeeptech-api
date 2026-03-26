"""Usage history router."""
from fastapi import APIRouter, Query

from app.core.deps import CurrentUser, DbDep
from app.schemas.usage import UsageLogOut
from app.services.usage_service import list_usage_for_user

router = APIRouter(prefix="/v1/usage", tags=["Usage"])


@router.get("", response_model=list[UsageLogOut])
async def get_usage(
    current_user: CurrentUser,
    db: DbDep,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[UsageLogOut]:
    """Return paginated usage history for the current user."""
    logs = await list_usage_for_user(db, current_user.id, limit=limit, offset=offset)
    return [UsageLogOut.model_validate(log) for log in logs]
