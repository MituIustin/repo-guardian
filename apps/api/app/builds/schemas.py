import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class ApiModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class BuildStepResponse(ApiModel):
    name: str
    status: str
    conclusion: str | None
    number: int
    started_at: datetime | None = None
    completed_at: datetime | None = None


class BuildJobResponse(ApiModel):
    id: uuid.UUID
    name: str
    status: str
    conclusion: str | None
    html_url: str
    started_at: datetime | None
    completed_at: datetime | None
    steps: list[BuildStepResponse]


class LogExcerptResponse(ApiModel):
    source_file: str | None
    start_line: int
    end_line: int
    content: str


class BuildResponse(ApiModel):
    id: uuid.UUID
    repository_id: uuid.UUID
    repository_full_name: str
    github_run_id: int
    workflow_name: str
    run_number: int
    run_attempt: int
    branch: str
    commit_sha: str
    status: str
    conclusion: str | None
    event: str
    html_url: str
    started_at: datetime | None
    completed_at: datetime | None
    updated_at: datetime
    jobs: list[BuildJobResponse]
    error_excerpt: LogExcerptResponse | None


class BuildsResponse(ApiModel):
    data: list[BuildResponse]


class RerunWorkflowRequest(ApiModel):
    mode: Literal["all", "failed"] = "all"


class RerunAccepted(ApiModel):
    status: str
