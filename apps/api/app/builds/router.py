import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import build_token_cipher, get_current_user
from app.build_jobs.models import BuildJob
from app.builds.realtime import build_realtime_hub
from app.builds.schemas import BuildsResponse, RerunAccepted, RerunWorkflowRequest
from app.builds.service import list_user_builds
from app.core.config import get_settings
from app.core.database import AsyncSessionFactory, get_db_session
from app.github.client import GitHubOAuthClient, GitHubOAuthError
from app.github_accounts.models import GitHubAccount
from app.github_app.dependencies import build_github_app_client
from app.repositories.models import Repository
from app.repository_connections.models import RepositoryConnection
from app.users.models import User
from app.workflow_runs.models import WorkflowRun

router = APIRouter(prefix="/api/builds", tags=["builds"])


def get_github_client() -> GitHubOAuthClient:
    return GitHubOAuthClient("", "", "")


@router.get("", response_model=BuildsResponse)
async def get_builds(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> BuildsResponse:
    return BuildsResponse(data=await list_user_builds(session, user.id))


async def _repository_token(
    session: AsyncSession, connection: RepositoryConnection
) -> str:
    if connection.installation_id:
        app_client = build_github_app_client(get_settings())
        token = await app_client.create_installation_token(connection.installation_id)
        return token.token
    account = await session.get(GitHubAccount, connection.github_account_id)
    if account is None or not account.access_token_encrypted:
        raise HTTPException(409, "No GitHub credential is available for this repository.")
    return build_token_cipher(get_settings()).decrypt(account.access_token_encrypted)


@router.post("/{build_id}/rerun", response_model=RerunAccepted, status_code=202)
async def rerun_build(
    build_id: uuid.UUID,
    payload: RerunWorkflowRequest,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    github_client: Annotated[GitHubOAuthClient, Depends(get_github_client)],
) -> RerunAccepted:
    row = (
        await session.execute(
            select(WorkflowRun, Repository, RepositoryConnection)
            .join(Repository, Repository.id == WorkflowRun.repository_id)
            .join(
                RepositoryConnection,
                RepositoryConnection.repository_id == Repository.id,
            )
            .where(
                WorkflowRun.id == build_id,
                RepositoryConnection.user_id == user.id,
                RepositoryConnection.is_active.is_(True),
            )
        )
    ).one_or_none()
    if row is None:
        raise HTTPException(404, "Build not found.")
    run, repository, connection = row
    if run.status != "completed":
        raise HTTPException(409, "Only completed workflow runs can be rerun.")
    if payload.mode == "failed" and run.conclusion == "success":
        raise HTTPException(409, "This workflow run has no failed jobs to rerun.")
    try:
        token = await _repository_token(session, connection)
        await github_client.rerun_workflow(
            token,
            repository.full_name,
            run.github_run_id,
            failed_jobs_only=payload.mode == "failed",
        )
    except GitHubOAuthError as error:
        raise HTTPException(
            502,
            "GitHub rejected the rerun request. Confirm that the GitHub App "
            "has Actions write permission.",
        ) from error
    return RerunAccepted(status="accepted")


@router.post("/jobs/{job_id}/rerun", response_model=RerunAccepted, status_code=202)
async def rerun_build_job(
    job_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    github_client: Annotated[GitHubOAuthClient, Depends(get_github_client)],
) -> RerunAccepted:
    row = (
        await session.execute(
            select(BuildJob, Repository, RepositoryConnection)
            .join(WorkflowRun, WorkflowRun.id == BuildJob.workflow_run_id)
            .join(Repository, Repository.id == WorkflowRun.repository_id)
            .join(
                RepositoryConnection,
                RepositoryConnection.repository_id == Repository.id,
            )
            .where(
                BuildJob.id == job_id,
                RepositoryConnection.user_id == user.id,
                RepositoryConnection.is_active.is_(True),
            )
        )
    ).one_or_none()
    if row is None:
        raise HTTPException(404, "Build job not found.")
    job, repository, connection = row
    if job.status != "completed":
        raise HTTPException(409, "Only completed jobs can be rerun.")
    try:
        token = await _repository_token(session, connection)
        await github_client.rerun_job(token, repository.full_name, job.github_job_id)
    except GitHubOAuthError as error:
        raise HTTPException(
            502,
            "GitHub rejected the rerun request. Confirm that the GitHub App "
            "has Actions write permission.",
        ) from error
    return RerunAccepted(status="accepted")


@router.websocket("/stream")
async def builds_websocket(websocket: WebSocket) -> None:
    raw_user_id = websocket.session.get("user_id")
    try:
        user_id = uuid.UUID(raw_user_id) if raw_user_id else None
    except ValueError:
        user_id = None
    if user_id is None:
        await websocket.close(code=4401)
        return
    async with AsyncSessionFactory() as session:
        if await session.get(User, user_id) is None:
            await websocket.close(code=4401)
            return
    await build_realtime_hub.connect(user_id, websocket)
    try:
        await websocket.send_json({"type": "builds.connected"})
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        build_realtime_hub.disconnect(user_id, websocket)
