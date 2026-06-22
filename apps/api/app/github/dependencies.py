from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import build_token_cipher, get_current_user
from app.auth.security import TokenEncryptionError
from app.core.config import Settings, get_settings
from app.core.database import get_db_session
from app.github_accounts.models import GitHubAccount
from app.users.models import User


@dataclass(frozen=True)
class AuthenticatedGitHub:
    account: GitHubAccount
    access_token: str


async def get_authenticated_github(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AuthenticatedGitHub:
    account = await session.scalar(
        select(GitHubAccount).where(GitHubAccount.user_id == user.id).limit(1)
    )
    if account is None or account.access_token_encrypted is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Reconnect GitHub before managing repositories.",
        )
    try:
        token = build_token_cipher(settings).decrypt(account.access_token_encrypted)
    except TokenEncryptionError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The GitHub connection could not be loaded.",
        ) from error
    return AuthenticatedGitHub(account=account, access_token=token)
