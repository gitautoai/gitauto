# Standard imports
import asyncio
import json
from typing import Any, cast
import urllib.parse
from uuid import uuid4

# Third-party imports
from fastapi import BackgroundTasks, FastAPI, Header, Request
from mangum import Mangum
from pydantic import BaseModel
import sentry_sdk
from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration

# Local imports
from config import ENV, GITHUB_WEBHOOK_SECRET, SENTRY_DSN, UTF8
from constants.general import PRODUCT_NAME
from payloads.aws.event_bridge_scheduler.event_types import EventBridgeSchedulerEvent
from payloads.aws.setup_installed_repository_event import SetupInstalledRepositoryEvent
from services.aws.cleanup_tmp import cleanup_tmp
from services.github.token.get_installation_token import get_installation_access_token
from services.github.utils.verify_webhook_signature import verify_webhook_signature
from services.sentry.before_send import before_send
from services.slack.slack_notify import slack_notify
from services.supabase.webhook_deliveries.insert_webhook_delivery import (
    insert_webhook_delivery,
)
from services.webhook.setup_installed_repository import setup_installed_repository
from services.webhook.schedule_handler import schedule_handler
from services.webhook.setup_handler import setup_handler
from services.webhook.webhook_handler import handle_webhook_event
from services.website.retarget_pr import retarget_pr
from services.website.sync_files_from_github_to_coverage import (
    sync_files_from_github_to_coverage,
)
from services.website.verify_api_key import verify_api_key
from utils.aws.extract_lambda_info import extract_lambda_info
from utils.logging.logging_config import (
    clear_state,
    logger,
    set_event_action,
    set_owner_repo,
    set_request_id,
    set_trigger,
)

# https://us-west-1.console.aws.amazon.com/lambda/home?region=us-west-1#/functions/pr-agent-prod?subtab=envVars&tab=configure
if ENV == "prod":
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        environment=ENV,
        integrations=[AwsLambdaIntegration()],
        traces_sample_rate=1.0,
        before_send=before_send,
    )

# Create FastAPI instance and Mangum handler. Mangum is a library that allows you to use FastAPI with AWS Lambda.
app = FastAPI()
mangum_handler = Mangum(app=app, lifespan="off")


# Here is an entry point for the AWS Lambda function. Mangum is a library that allows you to use FastAPI with AWS Lambda.
def handler(event, context):
    clear_state()  # Prevent metadata from previous invocation bleeding into this one on warm starts
    cleanup_tmp()  # Clean at START (not end) so it runs even if previous invocation crashed/timed out
    set_request_id(getattr(context, "aws_request_id", "local"))

    # For per-repo processing (dispatched by process_repositories)
    if "triggerType" in event and event["triggerType"] == "setup_installed_repository":
        event = cast(SetupInstalledRepositoryEvent, event)
        owner_name = event["owner_name"]
        repo_name = event["repo_name"]
        set_owner_repo(owner_name, repo_name)
        logger.info("handler: dispatching setup_installed_repository event")
        setup_installed_repository(
            owner_id=event["owner_id"],
            owner_name=owner_name,
            owner_type=event["owner_type"],
            repo_id=event["repo_id"],
            repo_name=repo_name,
            installation_id=event["installation_id"],
            user_id=event["user_id"],
            user_name=event["user_name"],
            sender_email=event["sender_email"],
            sender_display_name=event["sender_display_name"],
        )
        return None

    # For scheduled event from EventBridge Scheduler
    if "triggerType" in event and event["triggerType"] == "schedule":
        event = cast(EventBridgeSchedulerEvent, event)
        owner_name = event.get("ownerName", "")
        repo_name = event.get("repoName", "")
        set_owner_repo(owner_name, repo_name)
        logger.info("EventBridge Scheduler invoked")
        thread_ts = slack_notify(
            f"Event Scheduler started for {owner_name}/{repo_name}"
        )

        pr_url = schedule_handler(event=event)
        if pr_url:
            logger.info("schedule_handler created PR %s", pr_url)
            slack_notify(f"Completed: {pr_url}", thread_ts)
        return None

    # Python 3.14 removed implicit event loop creation in asyncio.get_event_loop(), which Mangum's HTTPCycle.__call__ still uses. Ensure one exists before each request.
    try:
        asyncio.get_event_loop()
    except RuntimeError:
        logger.info("No event loop found, creating one for Mangum")
        asyncio.set_event_loop(asyncio.new_event_loop())

    # mangum_handler converts requests from API Gateway to FastAPI routing system
    logger.info("handler: delegating to mangum_handler")
    return mangum_handler(event=event, context=context)


@app.post(path="/webhook")
async def handle_webhook(request: Request) -> dict[str, str]:
    event_name: str = request.headers.get("X-GitHub-Event", "Event not specified")
    delivery_id: str = request.headers.get("X-GitHub-Delivery", "No delivery ID")

    # Deduplicate webhook delivery using atomic database insert (None = DB error, still process)
    if insert_webhook_delivery(delivery_id=delivery_id, event_name=event_name) is False:
        logger.info(
            "Duplicate webhook ignored - delivery_id=%s event=%s",
            delivery_id,
            event_name,
        )
        return {"message": "Duplicate webhook ignored"}

    # Extract Lambda context information if available
    lambda_info = extract_lambda_info(request)

    # Validate if the webhook signature comes from GitHub
    await verify_webhook_signature(request=request, secret=GITHUB_WEBHOOK_SECRET)

    # Process the webhook event but never raise an exception as some event_name like "marketplace_purchase" doesn't have a payload
    try:
        request_body: bytes = await request.body()
    except Exception as e:  # pylint: disable=broad-except
        logger.error("Error reading request body: %s", e)
        request_body = b""

    payload: Any = {}
    try:
        # First try to parse the body as JSON
        payload = json.loads(s=request_body.decode(encoding=UTF8))
    except json.JSONDecodeError:
        # If JSON parsing fails, treat the body as URL-encoded
        decoded_body: dict[str, list[str]] = urllib.parse.parse_qs(
            qs=request_body.decode(encoding=UTF8)
        )
        if "payload" in decoded_body:
            logger.info("handle_webhook: URL-encoded payload wrapper detected")
            try:
                payload = json.loads(s=decoded_body["payload"][0])
            except json.JSONDecodeError:
                # If URL-encoded payload contains invalid JSON, use empty payload
                payload = {}
    except Exception as e:  # pylint: disable=broad-except
        logger.error("Error parsing JSON payload: %s", e)

    # Add delivery_id to lambda_info for debugging
    if lambda_info is None:
        logger.info("handle_webhook: lambda_info absent; initializing")
        lambda_info = {}
    lambda_info["delivery_id"] = delivery_id

    # Set logging context for owner/repo (most webhook payloads have repository field)
    repository = payload.get("repository", {})
    if repository:
        logger.info("handle_webhook: setting owner/repo context from payload")
        set_owner_repo(
            repository.get("owner", {}).get("login", ""), repository.get("name", "")
        )

    await handle_webhook_event(
        event_name=event_name, payload=payload, lambda_info=lambda_info
    )
    logger.info("handle_webhook: delivery_id=%s processed", delivery_id)
    return {"message": "Webhook processed successfully"}


@app.get(path="/")
async def root() -> dict[str, str]:
    logger.info("root: returning product name")
    return {"message": PRODUCT_NAME}


class SyncFilesRequest(BaseModel):
    branch: str
    owner_id: int
    repo_id: int
    user_name: str


@app.post(path="/api/{owner}/{repo}/sync_files_from_github_to_coverage")
async def api_sync_files_from_github_to_coverage(
    owner: str,
    repo: str,
    body: SyncFilesRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Header(..., alias="X-API-Key"),
):
    """Sync repository files from local clone to coverage database. Returns immediately via background_tasks.add_task."""
    background_tasks.add_task(
        sync_files_from_github_to_coverage,
        owner=owner,
        repo=repo,
        branch=body.branch,
        owner_id=body.owner_id,
        repo_id=body.repo_id,
        user_name=body.user_name,
        api_key=api_key,
    )
    logger.info("api_sync_files_from_github_to_coverage: queued")
    return {"status": "syncing"}


class RetargetRequest(BaseModel):
    installation_id: int
    new_base_branch: str
    pr_number: int


@app.post(path="/api/{owner}/{repo}/retarget_pr")
async def api_retarget_pr(
    owner: str,
    repo: str,
    body: RetargetRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Header(..., alias="X-API-Key"),
):
    """Retarget a PR to a new base branch. Returns immediately via background_tasks.add_task."""
    verify_api_key(api_key)
    set_request_id(str(uuid4()))
    set_owner_repo(owner, repo)
    set_event_action("website", "retarget_pr")
    set_trigger("retarget")

    token = get_installation_access_token(installation_id=body.installation_id)
    background_tasks.add_task(
        retarget_pr,
        owner_name=owner,
        repo_name=repo,
        token=token,
        new_base_branch=body.new_base_branch,
        pr_number=body.pr_number,
        installation_id=body.installation_id,
    )
    logger.info("api_retarget_pr: queued PR #%s", body.pr_number)
    return {"status": "processing"}


@app.post(path="/api/{owner}/{repo}/setup_coverage_workflow")
async def setup_coverage_workflow(
    owner: str,
    repo: str,
    token: str = Header(..., alias="X-GitHub-Token"),
    api_key: str = Header(..., alias="X-API-Key"),
    sender_id: int = Header(0, alias="X-Sender-Id"),
    sender_name: str = Header("", alias="X-Sender-Name"),
    source: str = Header("", alias="X-Source"),
):
    verify_api_key(api_key)
    logger.info("setup_coverage_workflow: invoking setup_handler")
    return await setup_handler(
        owner_name=owner,
        repo_name=repo,
        token=token,
        sender_id=sender_id,
        sender_name=sender_name,
        source=source,
    )
