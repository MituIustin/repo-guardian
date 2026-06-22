import logging
import secrets
from typing import Annotated
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import (
    build_token_cipher,
    get_current_user,
    get_github_oauth_client,
)
from app.auth.schemas import CurrentUserResponse, LogoutResponse
from app.auth.service import persist_github_login
from app.core.config import Settings, get_settings
from app.core.database import get_db_session
from app.github.client import GitHubOAuthClient, GitHubOAuthError
from app.github_accounts.models import GitHubAccount
from app.users.models import User

router = APIRouter(prefix="/api/auth", tags=["auth"])
logger = logging.getLogger(__name__)


@router.get("/github/login", response_class=RedirectResponse)
async def github_login(
    request: Request,
    github_client: Annotated[GitHubOAuthClient, Depends(get_github_oauth_client)],
) -> RedirectResponse:
    oauth_state = secrets.token_urlsafe(32)
    request.session["github_oauth_state"] = oauth_state
    return RedirectResponse(github_client.authorization_url(oauth_state))


@router.get("/github/callback", response_class=RedirectResponse)
async def github_callback(
    request: Request,
    github_client: Annotated[GitHubOAuthClient, Depends(get_github_oauth_client)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_settings)],
    code: Annotated[str | None, Query()] = None,
    state: Annotated[str | None, Query()] = None,
    error: Annotated[str | None, Query()] = None,
) -> RedirectResponse:
    expected_state = request.session.pop("github_oauth_state", None)
    if error:
        return _frontend_redirect(settings.frontend_url, "denied")
    state_is_valid = state and expected_state and secrets.compare_digest(state, expected_state)
    if not code or not state_is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GitHub OAuth state is invalid or expired.",
        )

    try:
        token_cipher = build_token_cipher(settings)
        token = await github_client.exchange_code(code)
        profile = await github_client.get_user(token.access_token)
        user = await persist_github_login(
            session=session,
            profile=profile,
            token=token,
            encrypted_access_token=token_cipher.encrypt(token.access_token),
        )
    except GitHubOAuthError as provider_error:
        logger.warning("GitHub OAuth callback failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="GitHub authentication could not be completed.",
        ) from provider_error
    except SQLAlchemyError as database_error:
        await session.rollback()
        logger.warning("GitHub OAuth persistence failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="GitHub authentication could not be saved.",
        ) from database_error

    request.session.clear()
    request.session["user_id"] = str(user.id)
    return _frontend_redirect(settings.frontend_url, "success")


@router.get("/me", response_model=CurrentUserResponse)
async def current_user(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> CurrentUserResponse:
    account = await session.scalar(
        select(GitHubAccount).where(GitHubAccount.user_id == user.id).limit(1)
    )
    if account is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The user does not have a GitHub account.",
        )
    return CurrentUserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        avatar_url=user.avatar_url,
        github_username=account.username,
    )


@router.post("/logout", response_model=LogoutResponse)
async def logout(request: Request) -> LogoutResponse:
    request.session.clear()
    return LogoutResponse(status="ok")


def _frontend_redirect(frontend_url: str, auth_status: str) -> RedirectResponse:
    return RedirectResponse(f"{frontend_url.rstrip('/')}?{urlencode({'auth': auth_status})}")
