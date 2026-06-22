import logging
import uuid
from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy import delete, select

from app.auth.dependencies import build_token_cipher
from app.build_jobs.models import BuildJob
from app.build_logs.models import BuildLogExcerpt
from app.build_logs.parser import LogArchiveError, extract_error_excerpt
from app.builds.realtime import build_realtime_hub
from app.builds.service import serialize_build
from app.core.config import get_settings
from app.core.database import AsyncSessionFactory
from app.github.client import GitHubOAuthClient, GitHubOAuthError
from app.github_accounts.models import GitHubAccount
from app.github_app.dependencies import build_github_app_client
from app.incidents.models import Incident
from app.repositories.models import Repository
from app.repositories.realtime import repository_realtime_hub
from app.repository_connections.models import RepositoryConnection
from app.webhooks.models import WebhookDelivery
from app.webhooks.schemas import WorkflowRunWebhook
from app.workflow_runs.models import WorkflowRun

logger = logging.getLogger(__name__)
FAILURE_CONCLUSIONS = {"failure", "timed_out", "action_required", "startup_failure"}


async def process_workflow_run_delivery(
    delivery_id: uuid.UUID, payload: WorkflowRunWebhook
) -> None:
    async with AsyncSessionFactory() as session:
        delivery = await session.get(WebhookDelivery, delivery_id)
        if delivery is None:
            return
        try:
            repository = await session.scalar(
                select(Repository).where(
                    Repository.github_repository_id == payload.repository.id
                )
            )
            if repository is None:
                await _finish_delivery(delivery, session, "ignored")
                return
            delivery.repository_id = repository.id
            all_connections = list(
                await session.scalars(
                    select(RepositoryConnection).where(
                        RepositoryConnection.repository_id == repository.id,
                        RepositoryConnection.is_active.is_(True),
                    )
                )
            )
            now = datetime.now(UTC)
            for connection in all_connections:
                connection.webhook_status = "active"
                connection.webhook_last_received_at = now
            connections = [
                item
                for item in all_connections
                if item.monitored_branch == payload.workflow_run.head_branch
            ]
            if not connections:
                await _finish_delivery(delivery, session, "ignored")
                for user_id in {item.user_id for item in all_connections}:
                    await repository_realtime_hub.notify(
                        user_id, "workflow_webhook_received"
                    )
                return

            run = await _upsert_workflow_run(session, repository, payload)
            account = await session.get(GitHubAccount, connections[0].github_account_id)
            warning: str | None = None
            token: str | None = None
            if payload.installation and any(
                item.installation_id == payload.installation.id for item in connections
            ):
                try:
                    app_client = build_github_app_client(get_settings())
                    installation_token = await app_client.create_installation_token(
                        payload.installation.id
                    )
                    token = installation_token.token
                except (GitHubOAuthError, HTTPException) as error:
                    logger.warning(
                        "GitHub App token creation failed for installation %s: %s",
                        payload.installation.id,
                        type(error).__name__,
                    )
            if token is None and account and account.access_token_encrypted:
                token = build_token_cipher(get_settings()).decrypt(
                    account.access_token_encrypted
                )
            if token:
                try:
                    github = GitHubOAuthClient("", "", "")
                    await _refresh_jobs(session, github, token, repository, run)
                    if run.conclusion in FAILURE_CONCLUSIONS:
                        await _store_failure_excerpt(
                            session, github, token, repository, run
                        )
                except (GitHubOAuthError, LogArchiveError, HTTPException) as error:
                    warning = "Workflow details or logs could not be downloaded."
                    logger.warning(
                        "GitHub workflow enrichment failed for run %s: %s",
                        run.github_run_id,
                        type(error).__name__,
                    )
            else:
                warning = "No GitHub credential was available for workflow enrichment."
            await _ensure_incident(session, repository, run)
            delivery.processing_status = "completed_with_warnings" if warning else "completed"
            delivery.error_message = warning
            delivery.processed_at = datetime.now(UTC)
            await session.commit()

            for user_id in {item.user_id for item in all_connections}:
                await repository_realtime_hub.notify(user_id, "workflow_webhook_received")

            build = await serialize_build(session, run, repository)
            await build_realtime_hub.broadcast(
                {item.user_id for item in connections},
                {
                    "type": "workflow_run.updated",
                    "data": build.model_dump(mode="json", by_alias=True),
                },
            )
        except Exception:
            await session.rollback()
            delivery = await session.get(WebhookDelivery, delivery_id)
            if delivery:
                delivery.processing_status = "failed"
                delivery.error_message = "Webhook processing failed."
                delivery.processed_at = datetime.now(UTC)
                await session.commit()
            logger.exception(
                "Workflow webhook processing failed for delivery %s", delivery_id
            )


async def _upsert_workflow_run(session, repository, payload) -> WorkflowRun:
    remote = payload.workflow_run
    run = await session.scalar(
        select(WorkflowRun).where(WorkflowRun.github_run_id == remote.id)
    )
    if run is None:
        run = WorkflowRun(repository_id=repository.id, github_run_id=remote.id)
        session.add(run)
    run.workflow_id = remote.workflow_id
    run.workflow_name = remote.name
    run.run_number = remote.run_number
    run.run_attempt = remote.run_attempt
    run.branch = remote.head_branch
    run.commit_sha = remote.head_sha
    run.status = remote.status
    run.conclusion = remote.conclusion
    run.trigger_event = remote.event
    run.html_url = remote.html_url
    run.started_at = remote.run_started_at
    run.completed_at = remote.updated_at if remote.status == "completed" else None
    await session.flush()
    return run


async def _refresh_jobs(session, github, token, repository, run) -> None:
    if run.status == "queued":
        return
    remote_jobs = await github.list_workflow_jobs(
        token, repository.full_name, run.github_run_id
    )
    for remote in remote_jobs:
        job = await session.scalar(
            select(BuildJob).where(BuildJob.github_job_id == remote.id)
        )
        if job is None:
            job = BuildJob(workflow_run_id=run.id, github_job_id=remote.id)
            session.add(job)
        job.name = remote.name
        job.status = remote.status
        job.conclusion = remote.conclusion
        job.started_at = remote.started_at
        job.completed_at = remote.completed_at
        job.runner_name = remote.runner_name
        job.html_url = remote.html_url
        job.steps = [step.model_dump(mode="json") for step in remote.steps]
    await session.flush()


async def _store_failure_excerpt(session, github, token, repository, run) -> None:
    archive = await github.download_workflow_logs(
        token, repository.full_name, run.github_run_id
    )
    extracted = extract_error_excerpt(archive)
    await session.execute(
        delete(BuildLogExcerpt).where(BuildLogExcerpt.workflow_run_id == run.id)
    )
    if extracted is None:
        return
    failed_job = await session.scalar(
        select(BuildJob)
        .where(
            BuildJob.workflow_run_id == run.id,
            BuildJob.conclusion.in_(FAILURE_CONCLUSIONS),
        )
        .limit(1)
    )
    session.add(
        BuildLogExcerpt(
            workflow_run_id=run.id,
            build_job_id=failed_job.id if failed_job else None,
            source_file=extracted.source_file,
            start_line=extracted.start_line,
            end_line=extracted.end_line,
            content=extracted.content,
        )
    )


async def _ensure_incident(session, repository, run) -> None:
    if run.conclusion not in FAILURE_CONCLUSIONS:
        return
    incident = await session.scalar(
        select(Incident).where(Incident.workflow_run_id == run.id).limit(1)
    )
    failed_job = await session.scalar(
        select(BuildJob)
        .where(
            BuildJob.workflow_run_id == run.id,
            BuildJob.conclusion.in_(FAILURE_CONCLUSIONS),
        )
        .limit(1)
    )
    if incident is None:
        incident = Incident(
            repository_id=repository.id,
            workflow_run_id=run.id,
            title=f"{run.workflow_name} failed on {run.branch}",
            status="open",
            severity="medium",
            category="unknown",
        )
        session.add(incident)
    incident.failed_job_id = failed_job.id if failed_job else None
    incident.summary = "A GitHub Actions workflow failed. Log evidence is ready for analysis."


async def _finish_delivery(delivery, session, status: str) -> None:
    delivery.processing_status = status
    delivery.processed_at = datetime.now(UTC)
    await session.commit()
