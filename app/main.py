"""
DCDeepTech API Gateway — FastAPI application entry point.
Registers all routers, middleware, CORS, and startup events.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.api import auth, api_keys, models, usage, billing, admin, openai_proxy


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run startup / shutdown logic around the app lifecycle."""
    # Future: warm connection pool, seed model catalog, etc.
    yield


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="OpenAI-compatible AI API gateway — Singapore region",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(api_keys.router)
app.include_router(models.router)
app.include_router(usage.router)
app.include_router(billing.router)
app.include_router(admin.router)
app.include_router(openai_proxy.router)


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"], include_in_schema=False)
async def health() -> JSONResponse:
    return JSONResponse({"status": "ok", "env": settings.app_env})


# ── Global exception handler (keeps error shape consistent) ──────────────────
from fastapi import Request
from fastapi.exceptions import RequestValidationError


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": str(exc.body)},
    )
