import logging
import uuid
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Response,
    WebSocket,
    WebSocketDisconnect,
)
from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.config import get_settings
from app.core.database import AsyncSessionFactory, get_db_session
from app.github.client import GitHubOAuthClient, GitHubOAuthError
from app.github.dependencies import AuthenticatedGitHub, get_authenticated_github
from app.github_app.dependencies import build_github_app_client
from app.github_app.models import GitHubAppInstallation
from app.repositories.models import Repository
from app.repositories.realtime import repository_realtime_hub
from app.repositories.schemas import (
    AvailableRepositoriesResponse,
    AvailableRepository,
    Branch,
    BranchesResponse,
    ConnectedRepositoriesResponse,
    ConnectedRepository,
    ConnectRepositoryRequest,
    DisconnectRepositoriesResponse,
    UpdateRepositoryRequest,
)
from app.repository_connections.models import RepositoryConnection
from app.users.models import User

router = APIRouter(prefix="/api/repositories", tags=["repositories"])
logger = logging.getLogger(__name__)


def get_github_client() -> GitHubOAuthClient:
    return GitHubOAuthClient("", "", "")


async def _connection_access_token(
    github: AuthenticatedGitHub, connection: RepositoryConnection
) -> str:
    if not connection.installation_id:
        return github.access_token
    app_client = build_github_app_client(get_settings())
    token = await app_client.create_installation_token(connection.installation_id)
    return token.token


async def _user_installation(
    session: AsyncSession, user_id: uuid.UUID, installation_id: int
) -> GitHubAppInstallation:
    installation = await session.scalar(
        select(GitHubAppInstallation).where(
            GitHubAppInstallation.user_id == user_id,
            GitHubAppInstallation.github_installation_id == installation_id,
            GitHubAppInstallation.status != "deleted",
        )
    )
    if installation is None:
        raise HTTPException(404, "GitHub source not found.")
    return installation


def _connected(
    connection: RepositoryConnection,
    repository: Repository,
    installation: GitHubAppInstallation | None = None,
) -> ConnectedRepository:
    return ConnectedRepository(
        id=repository.id,
        github_repository_id=repository.github_repository_id,
        name=repository.name,
        full_name=repository.full_name,
        visibility=repository.visibility,
        html_url=repository.html_url,
        default_branch=repository.default_branch,
        monitored_branch=connection.monitored_branch,
        is_active=connection.is_active,
        connected_at=connection.created_at,
        webhook_status=connection.webhook_status,
        webhook_last_received_at=connection.webhook_last_received_at,
        installation_id=connection.installation_id,
        installation_account_login=(installation.account_login if installation else None),
        installation_account_type=(installation.account_type if installation else None),
    )


@router.get("", response_model=ConnectedRepositoriesResponse)
async def list_connected_repositories(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ConnectedRepositoriesResponse:
    rows = (
        await session.execute(
            select(RepositoryConnection, Repository, GitHubAppInstallation)
            .join(Repository, Repository.id == RepositoryConnection.repository_id)
            .outerjoin(
                GitHubAppInstallation,
                GitHubAppInstallation.github_installation_id
                == RepositoryConnection.installation_id,
            )
            .where(RepositoryConnection.user_id == user.id)
            .where(RepositoryConnection.is_active.is_(True))
            .order_by(Repository.full_name)
        )
    ).all()
    return ConnectedRepositoriesResponse(data=[_connected(*row) for row in rows])


@router.websocket("/stream")
async def repositories_websocket(websocket: WebSocket) -> None:
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
    await repository_realtime_hub.connect(user_id, websocket)
    try:
        await websocket.send_json({"type": "repositories.connected"})
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        repository_realtime_hub.disconnect(user_id, websocket)


@router.delete("", response_model=DisconnectRepositoriesResponse)
async def disconnect_all_repositories(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> DisconnectRepositoriesResponse:
    result = await session.execute(
        update(RepositoryConnection)
        .where(
            RepositoryConnection.user_id == user.id,
            RepositoryConnection.is_active.is_(True),
        )
        .values(is_active=False)
    )
    await session.execute(
        update(GitHubAppInstallation)
        .where(GitHubAppInstallation.user_id == user.id)
        .values(monitoring_enabled=False)
    )
    await session.commit()
    await repository_realtime_hub.notify(user.id, "all_repositories_disconnected")
    return DisconnectRepositoriesResponse(
        status="disconnected", disconnected_count=result.rowcount or 0
    )


@router.get("/available", response_model=AvailableRepositoriesResponse)
async def list_available_repositories(
    github: Annotated[AuthenticatedGitHub, Depends(get_authenticated_github)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    github_client: Annotated[GitHubOAuthClient, Depends(get_github_client)],
    installation_id: Annotated[int | None, Query(gt=0)] = None,
) -> AvailableRepositoriesResponse:
    connected_ids = set(
        await session.scalars(
            select(Repository.github_repository_id)
            .join(RepositoryConnection)
            .where(
                RepositoryConnection.user_id == github.account.user_id,
                RepositoryConnection.is_active.is_(True),
            )
        )
    )
    try:
        if installation_id:
            await _user_installation(
                session, github.account.user_id, installation_id
            )
            app_client = build_github_app_client(get_settings())
            repositories = await app_client.list_installation_repositories(
                installation_id
            )
        else:
            repositories = await github_client.list_repositories(github.access_token)
    except GitHubOAuthError as error:
        raise _github_error(error) from error
    return AvailableRepositoriesResponse(
        data=[
            AvailableRepository(
                github_repository_id=item.id,
                name=item.name,
                full_name=item.full_name,
                private=item.private,
                visibility=item.visibility,
                html_url=item.html_url,
                default_branch=item.default_branch,
                updated_at=item.updated_at,
                is_connected=item.id in connected_ids,
            )
            for item in repositories
        ]
    )


@router.get("/available/{github_repository_id}/branches", response_model=BranchesResponse)
async def list_repository_branches(
    github_repository_id: int,
    github: Annotated[AuthenticatedGitHub, Depends(get_authenticated_github)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    github_client: Annotated[GitHubOAuthClient, Depends(get_github_client)],
    installation_id: Annotated[int | None, Query(gt=0)] = None,
) -> BranchesResponse:
    try:
        if installation_id:
            await _user_installation(
                session, github.account.user_id, installation_id
            )
            app_client = build_github_app_client(get_settings())
            access_token = (
                await app_client.create_installation_token(installation_id)
            ).token
            repository = await github_client.get_repository(
                access_token, github_repository_id
            )
        else:
            row = (
                await session.execute(
                    select(RepositoryConnection, Repository)
                    .join(
                        Repository,
                        Repository.id == RepositoryConnection.repository_id,
                    )
                    .where(
                        RepositoryConnection.user_id == github.account.user_id,
                        Repository.github_repository_id == github_repository_id,
                    )
                )
            ).one_or_none()
            if row:
                connection, repository = row
                access_token = await _connection_access_token(github, connection)
            else:
                repository = await github_client.get_repository(
                    github.access_token, github_repository_id
                )
                access_token = github.access_token
        branches = await github_client.list_branches(
            access_token, repository.full_name
        )
    except GitHubOAuthError as error:
        raise _github_error(error) from error
    return BranchesResponse(data=[Branch(name=item.name) for item in branches])


@router.post("/connect", response_model=ConnectedRepository, status_code=201)
async def connect_repository(
    payload: ConnectRepositoryRequest,
    github: Annotated[AuthenticatedGitHub, Depends(get_authenticated_github)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    github_client: Annotated[GitHubOAuthClient, Depends(get_github_client)],
) -> ConnectedRepository:
    try:
        access_token = github.access_token
        if payload.installation_id:
            await _user_installation(
                session, github.account.user_id, payload.installation_id
            )
            app_client = build_github_app_client(get_settings())
            access_token = (
                await app_client.create_installation_token(payload.installation_id)
            ).token
        remote = await github_client.get_repository(
            access_token, payload.github_repository_id
        )
        branches = await github_client.list_branches(access_token, remote.full_name)
        if payload.monitored_branch not in {branch.name for branch in branches}:
            raise HTTPException(status_code=422, detail="The selected branch does not exist.")
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
        connection = await session.scalar(
            select(RepositoryConnection).where(
                RepositoryConnection.user_id == github.account.user_id,
                RepositoryConnection.repository_id == repository.id,
            )
        )
        if connection is None:
            connection = RepositoryConnection(
                user_id=github.account.user_id,
                repository_id=repository.id,
                github_account_id=github.account.id,
            )
            session.add(connection)
        connection.monitored_branch = payload.monitored_branch
        connection.is_active = True
        connection.installation_id = payload.installation_id
        connection.webhook_status = (
            "configured" if payload.installation_id else "not_configured"
        )
        await session.commit()
        await session.refresh(connection)
        await repository_realtime_hub.notify(
            github.account.user_id, "repository_connected"
        )
        return _connected(connection, repository)
    except HTTPException:
        await session.rollback()
        raise
    except GitHubOAuthError as error:
        await session.rollback()
        raise _github_error(error) from error
    except SQLAlchemyError as error:
        await session.rollback()
        logger.warning("Repository connection persistence failed")
        raise HTTPException(500, "The repository connection could not be saved.") from error


@router.patch("/{repository_id}", response_model=ConnectedRepository)
async def update_repository_connection(
    repository_id: uuid.UUID,
    payload: UpdateRepositoryRequest,
    github: Annotated[AuthenticatedGitHub, Depends(get_authenticated_github)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    github_client: Annotated[GitHubOAuthClient, Depends(get_github_client)],
) -> ConnectedRepository:
    row = (
        await session.execute(
            select(RepositoryConnection, Repository)
            .join(Repository)
            .where(
                Repository.id == repository_id,
                RepositoryConnection.user_id == github.account.user_id,
            )
        )
    ).one_or_none()
    if row is None:
        raise HTTPException(404, "Repository connection not found.")
    connection, repository = row
    try:
        access_token = await _connection_access_token(github, connection)
        branches = await github_client.list_branches(access_token, repository.full_name)
        if payload.monitored_branch not in {branch.name for branch in branches}:
            raise HTTPException(422, "The selected branch does not exist.")
        connection.monitored_branch = payload.monitored_branch
        await session.commit()
        installation = None
        if connection.installation_id:
            installation = await session.scalar(
                select(GitHubAppInstallation).where(
                    GitHubAppInstallation.github_installation_id
                    == connection.installation_id
                )
            )
        await repository_realtime_hub.notify(
            github.account.user_id, "repository_updated"
        )
        return _connected(connection, repository, installation)
    except HTTPException:
        await session.rollback()
        raise
    except GitHubOAuthError as error:
        await session.rollback()
        raise _github_error(error) from error


@router.delete("/{repository_id}", status_code=204)
async def disconnect_repository(
    repository_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> Response:
    result = await session.execute(
        update(RepositoryConnection)
        .where(
            RepositoryConnection.user_id == user.id,
            RepositoryConnection.repository_id == repository_id,
        )
        .values(is_active=False)
    )
    if result.rowcount == 0:
        raise HTTPException(404, "Repository connection not found.")
    await session.commit()
    await repository_realtime_hub.notify(user.id, "repository_disconnected")
    return Response(status_code=204)


def _github_error(error: GitHubOAuthError) -> HTTPException:
    logger.warning("GitHub repository request failed: %s", type(error).__name__)
    return HTTPException(502, "GitHub repository data could not be loaded.")
