"""
OpenAI-compatible proxy endpoint.

Clients authenticate with an API key (dcdt_sk_live_...) via Bearer token —
NOT with a JWT. This matches how OpenAI SDK clients send requests.
"""
from fastapi import APIRouter, HTTPException, Request, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.deps import DbDep
from app.schemas.chat import ChatCompletionRequest
from app.services.openai_proxy_service import ProxyError, handle_chat_completion

router = APIRouter(tags=["OpenAI Proxy"])

# Separate bearer scheme so Swagger shows the correct auth hint for proxy routes
proxy_bearer = HTTPBearer(auto_error=True)


@router.post("/v1/chat/completions")
async def chat_completions(
    request: Request,
    body: ChatCompletionRequest,
    db: DbDep,
    credentials: HTTPAuthorizationCredentials = Security(proxy_bearer),
) -> dict:
    """
    OpenAI-compatible chat completion endpoint.

    Authentication:
        Authorization: Bearer dcdt_sk_live_<your_key>

    The model field must match a public_name in the model catalog.
    Usage is debited from your wallet in real time.
    """
    client_ip: str | None = request.headers.get("X-Forwarded-For") or (
        request.client.host if request.client else None
    )

    try:
        response = await handle_chat_completion(
            db=db,
            raw_api_key=credentials.credentials,
            request=body,
            client_ip=client_ip,
        )
    except ProxyError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)

    return response
