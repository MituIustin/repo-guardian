import json
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Request
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.database import get_db_session
from app.github_app.schemas import InstallationEvent
from app.github_app.service import process_installation_delivery
from app.webhooks.models import WebhookDelivery
from app.webhooks.schemas import WebhookAccepted, WorkflowRunWebhook
from app.webhooks.security import verify_github_signature
from app.webhooks.service import process_workflow_run_delivery

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])
MAX_WEBHOOK_BYTES = 1_000_000


@router.post("/github", response_model=WebhookAccepted, status_code=202)
async def github_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_settings)],
    github_event: Annotated[str | None, Header(alias="X-GitHub-Event")] = None,
    github_delivery: Annotated[str | None, Header(alias="X-GitHub-Delivery")] = None,
    github_signature: Annotated[str | None, Header(alias="X-Hub-Signature-256")] = None,
) -> WebhookAccepted:
    secret = (
        settings.github_webhook_secret.get_secret_value()
        if settings.github_webhook_secret
        else ""
    )
    if not secret:
        raise HTTPException(503, "GitHub webhooks are not configured.")
    body = await request.body()
    if len(body) > MAX_WEBHOOK_BYTES:
        raise HTTPException(413, "The GitHub webhook payload is too large.")
    if not verify_github_signature(body, github_signature, secret):
        raise HTTPException(401, "The GitHub webhook signature is invalid.")
    if not github_event or not github_delivery:
        raise HTTPException(400, "Required GitHub webhook headers are missing.")
    duplicate = await session.scalar(
        select(WebhookDelivery).where(
            WebhookDelivery.github_delivery_id == github_delivery
        )
    )
    if duplicate:
        return WebhookAccepted(status="duplicate")
    try:
        raw_payload = json.loads(body)
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise HTTPException(400, "The GitHub webhook payload is invalid.") from error

    delivery = WebhookDelivery(
        github_delivery_id=github_delivery,
        event_type=github_event,
        signature_verified=True,
        processing_status="pending",
        received_at=datetime.now(UTC),
    )
    session.add(delivery)
    try:
        await session.commit()
        await session.refresh(delivery)
    except IntegrityError:
        await session.rollback()
        return WebhookAccepted(status="duplicate")

    if github_event in {"installation", "installation_repositories"}:
        try:
            event = InstallationEvent.model_validate(raw_payload)
        except ValidationError as error:
            delivery.processing_status = "failed"
            delivery.error_message = "The GitHub App installation payload is invalid."
            delivery.processed_at = datetime.now(UTC)
            await session.commit()
            raise HTTPException(422, "The installation payload is invalid.") from error
        background_tasks.add_task(
            process_installation_delivery,
            delivery.id,
            github_event,
            event.action,
            event.installation.id,
        )
        return WebhookAccepted(status="accepted")
    if github_event != "workflow_run":
        delivery.processing_status = "ignored"
        delivery.processed_at = datetime.now(UTC)
        await session.commit()
        return WebhookAccepted(status="ignored")
    try:
        payload = WorkflowRunWebhook.model_validate(raw_payload)
    except ValidationError as error:
        delivery.processing_status = "failed"
        delivery.error_message = "The workflow_run payload is invalid."
        delivery.processed_at = datetime.now(UTC)
        await session.commit()
        raise HTTPException(422, "The workflow_run payload is invalid.") from error
    background_tasks.add_task(process_workflow_run_delivery, delivery.id, payload)
    return WebhookAccepted(status="accepted")
