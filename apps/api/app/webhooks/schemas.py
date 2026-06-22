from datetime import datetime

from pydantic import BaseModel


class WebhookRepository(BaseModel):
    id: int
    full_name: str


class WebhookHeadCommit(BaseModel):
    id: str


class WebhookInstallation(BaseModel):
    id: int


class WorkflowRunPayload(BaseModel):
    id: int
    workflow_id: int | None = None
    name: str
    run_number: int
    run_attempt: int = 1
    head_branch: str
    head_sha: str
    status: str
    conclusion: str | None = None
    event: str
    html_url: str
    run_started_at: datetime | None = None
    updated_at: datetime | None = None


class WorkflowRunWebhook(BaseModel):
    action: str
    repository: WebhookRepository
    workflow_run: WorkflowRunPayload
    installation: WebhookInstallation | None = None


class WebhookAccepted(BaseModel):
    status: str
