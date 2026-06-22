import uuid
from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import AsyncSessionFactory
from app.github_accounts.models import GitHubAccount
from app.github_app.client import GitHubAppClient
from app.github_app.dependencies import build_github_app_client
from app.github_app.models import GitHubAppInstallation
from app.repositories.models import Repository
from app.repositories.realtime import repository_realtime_hub
from app.repository_connections.models import RepositoryConnection


async def synchronize_installation(
    session: AsyncSession,
    client: GitHubAppClient,
    user_id: uuid.UUID,
    installation_id: int,
    enable_monitoring: bool | None = None,
) -> GitHubAppInstallation:
    remote_installation = await client.get_installation(installation_id)
    remote_repositories = await client.list_installation_repositories(installation_id)
    installation = await session.scalar(
        select(GitHubAppInstallation).where(
            GitHubAppInstallation.github_installation_id == installation_id
        )
    )
    was_monitoring_enabled = (
        installation.monitoring_enabled if installation is not None else False
    )
    if installation is not None and installation.user_id != user_id:
        raise HTTPException(409, "This GitHub App installation is already linked.")
    if installation is None:
        installation = GitHubAppInstallation(
            user_id=user_id,
            github_installation_id=installation_id,
            monitoring_enabled=enable_monitoring is not False,
        )
        session.add(installation)
    elif enable_monitoring is not None:
        installation.monitoring_enabled = enable_monitoring
    installation.account_id = remote_installation.account.id
    installation.account_login = remote_installation.account.login
    installation.account_type = remote_installation.account.type
    installation.repository_selection = remote_installation.repository_selection
    installation.status = "suspended" if remote_installation.suspended_at else "active"
    installation.suspended_at = remote_installation.suspended_at
    installation.last_synced_at = datetime.now(UTC)

    github_account = await session.scalar(
        select(GitHubAccount).where(GitHubAccount.user_id == user_id).limit(1)
    )
    if github_account is None:
        raise HTTPException(409, "A GitHub identity is required before installation.")

    synchronized_repository_ids: set[uuid.UUID] = set()
    for remote in remote_repositories:
        repository = await session.scalar(
            select(Repository).where(Repository.github_repository_id == remote.id)
        )
        if repository is None:
            repository = Repository(github_repository_id=remote.id)
            session.add(repository)
        repository.owner = remote.owner.login
        repository.name = remote.name
        repository.full_name = remote.full_name
        repository.default_branch = remote.default_branch
        repository.visibility = remote.visibility
        repository.html_url = remote.html_url
        await session.flush()
        synchronized_repository_ids.add(repository.id)

        if not installation.monitoring_enabled:
            continue

        connection = await session.scalar(
            select(RepositoryConnection).where(
                RepositoryConnection.user_id == user_id,
                RepositoryConnection.repository_id == repository.id,
            )
        )
        if connection is None:
            connection = RepositoryConnection(
                user_id=user_id,
                repository_id=repository.id,
                github_account_id=github_account.id,
                monitored_branch=repository.default_branch,
            )
            session.add(connection)
        elif enable_monitoring is True and not was_monitoring_enabled:
            connection.is_active = True
        connection.installation_id = installation_id
        connection.webhook_status = "configured"

    linked_connections = list(
        await session.scalars(
            select(RepositoryConnection).where(
                RepositoryConnection.user_id == user_id,
                RepositoryConnection.installation_id == installation_id,
            )
        )
    )
    for connection in linked_connections:
        if connection.repository_id not in synchronized_repository_ids:
            connection.installation_id = None
            connection.is_active = False
            connection.webhook_status = "not_configured"

    await session.commit()
    await session.refresh(installation)
    await repository_realtime_hub.notify(user_id, "installation_synchronized")
    return installation


async def process_installation_delivery(
    delivery_id: uuid.UUID, event_type: str, action: str, installation_id: int
) -> None:
    from app.webhooks.models import WebhookDelivery

    async with AsyncSessionFactory() as session:
        delivery = await session.get(WebhookDelivery, delivery_id)
        installation = await session.scalar(
            select(GitHubAppInstallation).where(
                GitHubAppInstallation.github_installation_id == installation_id
            )
        )
        if delivery is None:
            return
        try:
            if installation is None:
                delivery.processing_status = "ignored"
            elif event_type == "installation_repositories":
                client = build_github_app_client(get_settings())
                await synchronize_installation(
                    session, client, installation.user_id, installation_id
                )
                delivery.processing_status = "completed"
            elif action == "deleted":
                installation.status = "deleted"
                linked = list(
                    await session.scalars(
                        select(RepositoryConnection).where(
                            RepositoryConnection.installation_id == installation_id
                        )
                    )
                )
                for connection in linked:
                    connection.installation_id = None
                    connection.webhook_status = "not_configured"
                delivery.processing_status = "completed"
            elif action in {"suspend", "suspended"}:
                installation.status = "suspended"
                linked = list(
                    await session.scalars(
                        select(RepositoryConnection).where(
                            RepositoryConnection.installation_id == installation_id
                        )
                    )
                )
                for connection in linked:
                    connection.webhook_status = "not_configured"
                delivery.processing_status = "completed"
            elif action in {"unsuspend", "unsuspended"}:
                installation.status = "active"
                installation.suspended_at = None
                linked = list(
                    await session.scalars(
                        select(RepositoryConnection).where(
                            RepositoryConnection.installation_id == installation_id
                        )
                    )
                )
                for connection in linked:
                    connection.webhook_status = "configured"
                delivery.processing_status = "completed"
            else:
                delivery.processing_status = "ignored"
            delivery.processed_at = datetime.now(UTC)
            await session.commit()
            await repository_realtime_hub.notify(
                installation.user_id, "installation_updated"
            )
        except Exception:
            await session.rollback()
            delivery = await session.get(WebhookDelivery, delivery_id)
            if delivery:
                delivery.processing_status = "failed"
                delivery.error_message = "GitHub App installation synchronization failed."
                delivery.processed_at = datetime.now(UTC)
                await session.commit()
