import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import TokenCipher, TokenEncryptionError
from app.core.config import Settings, get_settings
from app.core.database import get_db_session
from app.github.client import GitHubOAuthClient
from app.users.models import User


def get_github_oauth_client(
    settings: Annotated[Settings, Depends(get_settings)],
) -> GitHubOAuthClient:
    if (
        not settings.github_client_id
        or not settings.github_client_secret
        or not settings.github_client_secret.get_secret_value()
    ):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GitHub OAuth is not configured.",
        )
    return GitHubOAuthClient(
        client_id=settings.github_client_id,
        client_secret=settings.github_client_secret.get_secret_value(),
        callback_url=settings.github_oauth_callback_url,
    )


def get_token_cipher(
    settings: Annotated[Settings, Depends(get_settings)],
) -> TokenCipher:
    return build_token_cipher(settings)


def build_token_cipher(settings: Settings) -> TokenCipher:
    if (
        settings.token_encryption_key is None
        or not settings.token_encryption_key.get_secret_value()
    ):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Token encryption is not configured.",
        )
    try:
        return TokenCipher(settings.token_encryption_key.get_secret_value())
    except TokenEncryptionError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Token encryption is not configured correctly.",
        ) from error


async def get_current_user(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> User:
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated.")
    try:
        parsed_user_id = uuid.UUID(user_id)
    except ValueError as error:
        request.session.clear()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication session is invalid.",
        ) from error

    user = await session.get(User, parsed_user_id)
    if user is None:
        request.session.clear()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated.")
    return user
