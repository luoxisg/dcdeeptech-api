"""API key management router."""
import uuid

from fastapi import APIRouter, HTTPException, status

from app.core.deps import CurrentUser, DbDep
from app.schemas.api_key import ApiKeyCreateRequest, ApiKeyCreatedResponse, ApiKeyOut
from app.services.api_key_service import create_api_key, list_api_keys, revoke_api_key

router = APIRouter(prefix="/v1/keys", tags=["API Keys"])


@router.get("", response_model=list[ApiKeyOut])
async def get_keys(current_user: CurrentUser, db: DbDep) -> list[ApiKeyOut]:
    """List all active API keys for the current user."""
    keys = await list_api_keys(db, current_user.id)
    return [ApiKeyOut.model_validate(k) for k in keys]


@router.post("", response_model=ApiKeyCreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_key(
    data: ApiKeyCreateRequest, current_user: CurrentUser, db: DbDep
) -> ApiKeyCreatedResponse:
    """
    Create a new API key.
    The full plaintext key is returned ONCE in this response.
    Store it securely — it cannot be retrieved again.
    """
    key_row, plaintext = await create_api_key(db, current_user, data)
    return ApiKeyCreatedResponse(
        id=key_row.id,
        name=key_row.name,
        key=plaintext,
        key_prefix=key_row.key_prefix,
        status=key_row.status,
        created_at=key_row.created_at,
        expires_at=key_row.expires_at,
    )


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_key(key_id: uuid.UUID, current_user: CurrentUser, db: DbDep) -> None:
    """Revoke (soft-delete) an API key. The key will immediately stop working."""
    deleted = await revoke_api_key(db, key_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")
