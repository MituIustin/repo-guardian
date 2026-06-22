from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.github.schemas import GitHubToken, GitHubUserProfile
from app.github_accounts.models import GitHubAccount
from app.users.models import User


async def persist_github_login(
    session: AsyncSession,
    profile: GitHubUserProfile,
    token: GitHubToken,
    encrypted_access_token: bytes,
) -> User:
    account = await session.scalar(
        select(GitHubAccount).where(GitHubAccount.github_user_id == profile.id)
    )

    if account is not None:
        user = await session.get(User, account.user_id)
        if user is None:
            raise RuntimeError("GitHub account references a missing user")
    else:
        user = None
        if profile.email:
            user = await session.scalar(select(User).where(User.email == profile.email))
        if user is None:
            user = User(email=profile.email, name=profile.name or profile.login)
            session.add(user)
            await session.flush()

        account = GitHubAccount(
            user_id=user.id,
            github_user_id=profile.id,
            username=profile.login,
        )
        session.add(account)

    user.name = profile.name or profile.login
    user.avatar_url = profile.avatar_url
    user.last_login_at = datetime.now(UTC)
    if user.email is None:
        user.email = profile.email

    account.username = profile.login
    account.display_name = profile.name
    account.avatar_url = profile.avatar_url
    account.access_token_encrypted = encrypted_access_token
    account.token_scope = token.scope
    account.token_type = token.token_type

    await session.commit()
    await session.refresh(user)
    return user

