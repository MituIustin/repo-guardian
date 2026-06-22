import logging
from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.database import get_db_session
from app.health.schemas import HealthResponse, ReadinessChecks, ReadinessResponse

router = APIRouter(prefix="/api", tags=["health"])
logger = logging.getLogger(__name__)


@router.get("/health", response_model=HealthResponse)
async def health(settings: Annotated[Settings, Depends(get_settings)]) -> HealthResponse:
    return HealthResponse(status="ok", service="repo-guardian-api", version=settings.app_version)


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    responses={status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ReadinessResponse}},
)
async def readiness(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> ReadinessResponse | JSONResponse:
    try:
        await session.execute(text("SELECT 1"))
    except Exception:
        logger.warning("Database readiness check failed")
        payload = ReadinessResponse(
            status="not_ready",
            service="repo-guardian-api",
            version=settings.app_version,
            checks=ReadinessChecks(database="unavailable"),
        )
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=payload.model_dump(),
        )

    return ReadinessResponse(
        status="ready",
        service="repo-guardian-api",
        version=settings.app_version,
        checks=ReadinessChecks(database="ok"),
    )
