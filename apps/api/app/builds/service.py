import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.build_jobs.models import BuildJob
from app.build_logs.models import BuildLogExcerpt
from app.builds.schemas import (
    BuildJobResponse,
    BuildResponse,
    BuildStepResponse,
    LogExcerptResponse,
)
from app.repositories.models import Repository
from app.repository_connections.models import RepositoryConnection
from app.workflow_runs.models import WorkflowRun


async def list_user_builds(
    session: AsyncSession, user_id: uuid.UUID, limit: int = 100
) -> list[BuildResponse]:
    rows = (
        await session.execute(
            select(WorkflowRun, Repository)
            .join(Repository, Repository.id == WorkflowRun.repository_id)
            .join(
                RepositoryConnection,
                RepositoryConnection.repository_id == Repository.id,
            )
            .where(
                RepositoryConnection.user_id == user_id,
                RepositoryConnection.is_active.is_(True),
            )
            .order_by(WorkflowRun.updated_at.desc())
            .limit(limit)
        )
    ).all()
    return [await serialize_build(session, run, repository) for run, repository in rows]


async def serialize_build(
    session: AsyncSession, run: WorkflowRun, repository: Repository
) -> BuildResponse:
    jobs = list(
        await session.scalars(
            select(BuildJob)
            .where(BuildJob.workflow_run_id == run.id)
            .order_by(BuildJob.started_at, BuildJob.name)
        )
    )
    excerpt = await session.scalar(
        select(BuildLogExcerpt)
        .where(BuildLogExcerpt.workflow_run_id == run.id)
        .order_by(BuildLogExcerpt.created_at.desc())
        .limit(1)
    )
    return BuildResponse(
        id=run.id,
        repository_id=repository.id,
        repository_full_name=repository.full_name,
        github_run_id=run.github_run_id,
        workflow_name=run.workflow_name,
        run_number=run.run_number,
        run_attempt=run.run_attempt,
        branch=run.branch,
        commit_sha=run.commit_sha,
        status=run.status,
        conclusion=run.conclusion,
        event=run.trigger_event,
        html_url=run.html_url,
        started_at=run.started_at,
        completed_at=run.completed_at,
        updated_at=run.updated_at,
        jobs=[
            BuildJobResponse(
                id=job.id,
                name=job.name,
                status=job.status,
                conclusion=job.conclusion,
                html_url=job.html_url,
                started_at=job.started_at,
                completed_at=job.completed_at,
                steps=[BuildStepResponse.model_validate(step) for step in job.steps],
            )
            for job in jobs
        ],
        error_excerpt=(
            LogExcerptResponse(
                source_file=excerpt.source_file,
                start_line=excerpt.start_line,
                end_line=excerpt.end_line,
                content=excerpt.content,
            )
            if excerpt
            else None
        ),
    )
