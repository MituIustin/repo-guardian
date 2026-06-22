from datetime import datetime

from pydantic import BaseModel, Field


class GitHubToken(BaseModel):
    access_token: str
    token_type: str = "bearer"
    scope: str = ""


class GitHubUserProfile(BaseModel):
    id: int
    login: str
    name: str | None = None
    email: str | None = None
    avatar_url: str | None = None


class GitHubEmail(BaseModel):
    email: str
    primary: bool
    verified: bool


class GitHubRepositoryOwner(BaseModel):
    login: str


class GitHubRepository(BaseModel):
    id: int
    name: str
    full_name: str
    owner: GitHubRepositoryOwner
    private: bool
    visibility: str
    html_url: str
    default_branch: str
    updated_at: datetime


class GitHubBranch(BaseModel):
    name: str


class GitHubJobStep(BaseModel):
    name: str
    status: str
    conclusion: str | None = None
    number: int
    started_at: datetime | None = None
    completed_at: datetime | None = None


class GitHubJob(BaseModel):
    id: int
    name: str
    status: str
    conclusion: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    runner_name: str | None = None
    html_url: str
    steps: list[GitHubJobStep] = Field(default_factory=list)
