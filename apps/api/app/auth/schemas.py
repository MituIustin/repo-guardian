import uuid

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CurrentUserResponse(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    id: uuid.UUID
    name: str
    email: str | None
    avatar_url: str | None
    github_username: str


class LogoutResponse(BaseModel):
    status: str
