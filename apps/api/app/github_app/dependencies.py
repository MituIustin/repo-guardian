from typing import Annotated

from fastapi import Depends, HTTPException

from app.core.config import Settings, get_settings
from app.github_app.client import GitHubAppClient, GitHubAppConfigurationError


def build_github_app_client(settings: Settings) -> GitHubAppClient:
    private_key = (
        settings.github_app_private_key_base64.get_secret_value()
        if settings.github_app_private_key_base64
        else ""
    )
    if not settings.github_app_id or not private_key:
        raise HTTPException(503, "GitHub App authentication is not configured.")
    try:
        return GitHubAppClient(settings.github_app_id, private_key)
    except GitHubAppConfigurationError as error:
        raise HTTPException(
            503, "GitHub App authentication is not configured correctly."
        ) from error


def get_github_app_client(
    settings: Annotated[Settings, Depends(get_settings)],
) -> GitHubAppClient:
    return build_github_app_client(settings)
