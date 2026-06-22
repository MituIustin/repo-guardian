from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.auth.router import router as auth_router
from app.builds.router import router as builds_router
from app.core.config import get_settings
from app.github_app.router import router as github_app_router
from app.health.router import router as health_router
from app.repositories.router import router as repositories_router
from app.webhooks.router import router as webhooks_router

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.frontend_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["*"],
)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret.get_secret_value(),
    session_cookie="repo_guardian_session",
    max_age=60 * 60 * 24 * 14,
    same_site="lax",
    https_only=settings.session_cookie_secure,
)
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(repositories_router)
app.include_router(builds_router)
app.include_router(webhooks_router)
app.include_router(github_app_router)
