import secrets
from typing import Annotated
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import func, select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.config import Settings, get_settings
from app.core.database import get_db_session
from app.github.client import GitHubOAuthError
from app.github_app.client import GitHubAppClient
from app.github_app.dependencies import get_github_app_client
from app.github_app.models import GitHubAppInstallation
from app.github_app.schemas import (
    GitHubAppActionResponse,
    GitHubAppInstallationStatus,
    GitHubAppStatus,
)
from app.github_app.service import synchronize_installation
from app.repositories.realtime import repository_realtime_hub
from app.repository_connections.models import RepositoryConnection
from app.users.models import User

router = APIRouter(prefix="/api/github-app", tags=["github-app"])


@router.get("/status", response_model=GitHubAppStatus)
async def github_app_status(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> GitHubAppStatus:
    configured = bool(
        settings.github_app_id
        and settings.github_app_slug
        and settings.github_app_private_key_base64
        and settings.github_app_private_key_base64.get_secret_value()
    )
    installations = list(
        await session.scalars(
            select(GitHubAppInstallation)
        .where(GitHubAppInstallation.user_id == user.id)
            .where(GitHubAppInstallation.status != "deleted")
            .order_by(GitHubAppInstallation.account_login)
        )
    )
    if not installations:
        return GitHubAppStatus(configured=configured, installed=False)
    counts = dict(
        (
            await session.execute(
                select(RepositoryConnection.installation_id, func.count())
                .where(
                    RepositoryConnection.user_id == user.id,
                    RepositoryConnection.installation_id.is_not(None),
                    RepositoryConnection.is_active.is_(True),
                )
                .group_by(RepositoryConnection.installation_id)
            )
        ).all()
    )
    installation_statuses = [
        GitHubAppInstallationStatus(
            installation_id=item.github_installation_id,
            account_login=item.account_login,
            account_type=item.account_type,
            repository_selection=item.repository_selection,
            status=item.status,
            monitoring_enabled=item.monitoring_enabled,
            repository_count=counts.get(item.github_installation_id, 0),
            last_synced_at=item.last_synced_at,
        )
        for item in installations
    ]
    return GitHubAppStatus(
        configured=configured,
        installed=True,
        total_repository_count=sum(item.repository_count for item in installation_statuses),
        installations=installation_statuses,
    )


@router.post(
    "/installations/{installation_id}/synchronize",
    response_model=GitHubAppActionResponse,
)
async def synchronize_github_app_installation(
    installation_id: int,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    client: Annotated[GitHubAppClient, Depends(get_github_app_client)],
) -> GitHubAppActionResponse:
    installation = await session.scalar(
        select(GitHubAppInstallation).where(
            GitHubAppInstallation.github_installation_id == installation_id,
            GitHubAppInstallation.user_id == user.id,
        )
    )
    if installation is None:
        raise HTTPException(404, "GitHub App installation not found.")
    try:
        await synchronize_installation(
            session, client, user.id, installation_id, enable_monitoring=True
        )
    except GitHubOAuthError as error:
        raise HTTPException(502, "GitHub App installation could not be synchronized.") from error
    return GitHubAppActionResponse(status="synchronized")


@router.delete(
    "/installations/{installation_id}/repositories",
    response_model=GitHubAppActionResponse,
)
async def disconnect_installation_repositories(
    installation_id: int,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> GitHubAppActionResponse:
    installation = await session.scalar(
        select(GitHubAppInstallation).where(
            GitHubAppInstallation.github_installation_id == installation_id,
            GitHubAppInstallation.user_id == user.id,
        )
    )
    if installation is None:
        raise HTTPException(404, "GitHub App installation not found.")
    await session.execute(
        update(RepositoryConnection)
        .where(
            RepositoryConnection.user_id == user.id,
            RepositoryConnection.installation_id == installation_id,
        )
        .values(is_active=False)
    )
    installation.monitoring_enabled = False
    await session.commit()
    await repository_realtime_hub.notify(user.id, "installation_disconnected")
    return GitHubAppActionResponse(status="disconnected")


@router.delete(
    "/installations/{installation_id}",
    response_model=GitHubAppActionResponse,
)
async def uninstall_github_app_account(
    installation_id: int,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    client: Annotated[GitHubAppClient, Depends(get_github_app_client)],
) -> GitHubAppActionResponse:
    installation = await session.scalar(
        select(GitHubAppInstallation).where(
            GitHubAppInstallation.github_installation_id == installation_id,
            GitHubAppInstallation.user_id == user.id,
            GitHubAppInstallation.status != "deleted",
        )
    )
    if installation is None:
        raise HTTPException(404, "GitHub App installation not found.")
    try:
        await client.delete_installation(installation_id)
    except GitHubOAuthError as error:
        raise HTTPException(502, "The GitHub App installation could not be removed.") from error
    await session.execute(
        update(RepositoryConnection)
        .where(
            RepositoryConnection.user_id == user.id,
            RepositoryConnection.installation_id == installation_id,
        )
        .values(is_active=False, webhook_status="not_configured")
    )
    installation.monitoring_enabled = False
    installation.status = "deleted"
    await session.commit()
    await repository_realtime_hub.notify(user.id, "installation_removed")
    return GitHubAppActionResponse(status="removed")


@router.get("/install", response_class=RedirectResponse)
async def install_github_app(
    request: Request,
    user: Annotated[User, Depends(get_current_user)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> RedirectResponse:
    del user
    if not (
        settings.github_app_id
        and settings.github_app_slug
        and settings.github_app_private_key_base64
        and settings.github_app_private_key_base64.get_secret_value()
    ):
        raise HTTPException(503, "GitHub App installation is not configured.")
    state = secrets.token_urlsafe(32)
    request.session["github_app_install_state"] = state
    query = urlencode({"state": state})
    return RedirectResponse(
        f"https://github.com/apps/{settings.github_app_slug}/installations/new?{query}"
    )


@router.get("/setup", response_class=RedirectResponse)
async def github_app_setup(
    request: Request,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    client: Annotated[GitHubAppClient, Depends(get_github_app_client)],
    settings: Annotated[Settings, Depends(get_settings)],
    installation_id: Annotated[int, Query(gt=0)],
    state: Annotated[str | None, Query()] = None,
) -> RedirectResponse:
    expected_state = request.session.pop("github_app_install_state", None)
    if not state or not expected_state or not secrets.compare_digest(state, expected_state):
        raise HTTPException(400, "GitHub App installation state is invalid or expired.")
    try:
        await synchronize_installation(
            session, client, user.id, installation_id, enable_monitoring=True
        )
    except GitHubOAuthError as error:
        raise HTTPException(502, "GitHub App installation could not be synchronized.") from error
    except SQLAlchemyError as error:
        await session.rollback()
        raise HTTPException(500, "GitHub App installation could not be saved.") from error
    return RedirectResponse(
        f"{settings.frontend_url.rstrip('/')}/repositories?github_app=installed"
    )
