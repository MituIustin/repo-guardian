from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from app.github.schemas import GitHubRepository


class GitHubInstallationAccount(BaseModel):
    id: int
    login: str
    type: str


class GitHubInstallation(BaseModel):
    id: int
    account: GitHubInstallationAccount
    repository_selection: str
    suspended_at: datetime | None = None


class InstallationToken(BaseModel):
    token: str
    expires_at: datetime


class InstallationRepositories(BaseModel):
    repositories: list[GitHubRepository]


class GitHubAppInstallationStatus(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    installation_id: int
    account_login: str
    account_type: str
    repository_selection: str
    status: str
    monitoring_enabled: bool
    repository_count: int
    last_synced_at: datetime | None


class GitHubAppStatus(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    configured: bool
    installed: bool
    total_repository_count: int = 0
    installations: list[GitHubAppInstallationStatus] = Field(default_factory=list)


class GitHubAppActionResponse(BaseModel):
    status: str


class InstallationEvent(BaseModel):
    action: str
    installation: GitHubInstallation


class InstallationRepositoriesEvent(BaseModel):
    action: str
    installation: GitHubInstallation
