"""
DCDeepTech API Gateway — FastAPI application entry point.
Registers all routers, middleware, CORS, and startup events.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_redoc_html
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.api import auth, api_keys, models, usage, billing, admin, openai_proxy


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="OpenAI-compatible AI API gateway — Singapore region",
    docs_url="/docs",
    redoc_url=None,
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(api_keys.router)
app.include_router(models.router)
app.include_router(usage.router)
app.include_router(billing.router)
app.include_router(admin.router)
app.include_router(openai_proxy.router)


@app.get("/redoc", include_in_schema=False)
async def custom_redoc():
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=f"{settings.app_name} - ReDoc",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@2/bundles/redoc.standalone.js",
    )


@app.get("/health", tags=["Health"], include_in_schema=False)
async def health() -> JSONResponse:
    return JSONResponse({"status": "ok", "env": settings.app_env})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": str(exc.body)},
    )