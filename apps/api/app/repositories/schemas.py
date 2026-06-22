import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class ApiModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class AvailableRepository(ApiModel):
    github_repository_id: int
    name: str
    full_name: str
    private: bool
    visibility: str
    html_url: str
    default_branch: str
    updated_at: datetime
    is_connected: bool


class ConnectedRepository(ApiModel):
    id: uuid.UUID
    github_repository_id: int
    name: str
    full_name: str
    visibility: str
    html_url: str
    default_branch: str
    monitored_branch: str
    is_active: bool
    webhook_status: Literal["not_configured", "configured", "active"]
    webhook_last_received_at: datetime | None
    connected_at: datetime
    installation_id: int | None
    installation_account_login: str | None
    installation_account_type: str | None


class Branch(ApiModel):
    name: str


class AvailableRepositoriesResponse(ApiModel):
    data: list[AvailableRepository]


class ConnectedRepositoriesResponse(ApiModel):
    data: list[ConnectedRepository]


class BranchesResponse(ApiModel):
    data: list[Branch]


class ConnectRepositoryRequest(ApiModel):
    github_repository_id: int
    monitored_branch: str = Field(min_length=1, max_length=255)
    installation_id: int | None = Field(default=None, gt=0)


class UpdateRepositoryRequest(ApiModel):
    monitored_branch: str = Field(min_length=1, max_length=255)


class DisconnectRepositoriesResponse(ApiModel):
    status: str
    disconnected_count: int
