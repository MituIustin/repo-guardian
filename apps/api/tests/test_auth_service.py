import uuid

import pytest

from app.auth.service import persist_github_login
from app.github.schemas import GitHubToken, GitHubUserProfile
from app.github_accounts.models import GitHubAccount
from app.users.models import User


class FakeSession:
    def __init__(self) -> None:
        self.added: list[object] = []
        self.committed = False

    async def scalar(self, _statement):
        return None

    def add(self, model: object) -> None:
        self.added.append(model)

    async def flush(self) -> None:
        for model in self.added:
            if isinstance(model, User) and model.id is None:
                model.id = uuid.uuid4()

    async def commit(self) -> None:
        self.committed = True

    async def refresh(self, _model: object) -> None:
        return None


@pytest.mark.asyncio
async def test_persist_github_login_creates_user_and_encrypted_account() -> None:
    session = FakeSession()
    profile = GitHubUserProfile(
        id=123,
        login="octocat",
        name="The Octocat",
        email="octocat@example.com",
        avatar_url="https://avatars.example/octocat.png",
    )
    token = GitHubToken(access_token="plain-token", token_type="bearer", scope="read:user")

    user = await persist_github_login(
        session=session,
        profile=profile,
        token=token,
        encrypted_access_token=b"encrypted-token",
    )

    account = next(model for model in session.added if isinstance(model, GitHubAccount))
    assert user.email == "octocat@example.com"
    assert account.user_id == user.id
    assert account.access_token_encrypted == b"encrypted-token"
    assert session.committed is True

