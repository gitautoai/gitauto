# Standard imports
import json
from typing import Any, cast
import urllib.parse

# Third-party imports
from fastapi import BackgroundTasks, FastAPI, Header, Request
from mangum import Mangum
from pydantic import BaseModel
import sentry_sdk
from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration

# Local imports
from config import ENV, GITHUB_WEBHOOK_SECRET, PRODUCT_NAME, SENTRY_DSN, UTF8
from payloads.aws.event_bridge_scheduler.event_types import EventBridgeSchedulerEvent
from services.github.utils.verify_webhook_signature import verify_webhook_signature
from services.slack.slack_notify import slack_notify
from services.supabase.webhook_deliveries.insert_webhook_delivery import (
    insert_webhook_delivery,
)
from services.efs.cleanup_stale_repos_on_efs import cleanup_stale_repos_on_efs
from services.aws.cleanup_tmp import cleanup_tmp
from services.efs.clone_and_install import clone_and_install
from services.webhook.schedule_handler import schedule_handler
from services.webhook.setup_handler import setup_handler
from services.webhook.webhook_handler import handle_webhook_event
from services.website.sync_files_from_github_to_coverage import (
    sync_files_from_github_to_coverage,
)
from services.website.verify_api_key import verify_api_key
from utils.aws.extract_lambda_info import extract_lambda_info
from utils.logging.logging_config import (
    clear_state,
    logger,
    set_owner_repo,
    set_request_id,
)

# https://us-west-1.console.aws.amazon.com/lambda/home?region=us-west-1#/functions/pr-agent-prod?subtab=envVars&tab=configure
if ENV == "prod":
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        environment=ENV,
        integrations=[AwsLambdaIntegration()],
        traces_sample_rate=1.0,
    )

# Create FastAPI instance and Mangum handler. Mangum is a library that allows you to use FastAPI with AWS Lambda.
app = FastAPI()
mangum_handler = Mangum(app=app, lifespan="off")


# Here is an entry point for the AWS Lambda function. Mangum is a library that allows you to use FastAPI with AWS Lambda.
def handler(event, context):
    clear_state()  # Prevent metadata from previous invocation bleeding into this one on warm starts
    cleanup_tmp()  # Clean at START (not end) so it runs even if previous invocation crashed/timed out
    set_request_id(getattr(context, "aws_request_id", "local"))

    # For EFS cleanup scheduled event
    if "triggerType" in event and event["triggerType"] == "cleanup":
        logger.info("EFS cleanup triggered")
        result = cleanup_stale_repos_on_efs()
        logger.info("EFS cleanup result: %s", result)
        return result

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

        result = schedule_handler(event=event)
        if result and result["status"] == "success":
            slack_notify("Completed", thread_ts)
        elif result:
            slack_notify(
                f"@channel Failed: {result.get('message', 'Unknown error')}",
                thread_ts,
            )
        return None

    # mangum_handler converts requests from API Gateway to FastAPI routing system
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
            try:
                payload = json.loads(s=decoded_body["payload"][0])
            except json.JSONDecodeError:
                # If URL-encoded payload contains invalid JSON, use empty payload
                payload = {}
    except Exception as e:  # pylint: disable=broad-except
        logger.error("Error parsing JSON payload: %s", e)

    # Add delivery_id to lambda_info for debugging
    if lambda_info is None:
        lambda_info = {}
    lambda_info["delivery_id"] = delivery_id

    # Set logging context for owner/repo (most webhook payloads have repository field)
    repository = payload.get("repository", {})
    if repository:
        set_owner_repo(
            repository.get("owner", {}).get("login", ""), repository.get("name", "")
        )

    await handle_webhook_event(
        event_name=event_name, payload=payload, lambda_info=lambda_info
    )
    return {"message": "Webhook processed successfully"}


@app.get(path="/")
async def root() -> dict[str, str]:
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
    token: str = Header(..., alias="X-GitHub-Token"),
    api_key: str = Header(..., alias="X-API-Key"),
):
    """Sync repository files from GitHub to coverage database. Returns immediately, runs in background."""
    background_tasks.add_task(
        sync_files_from_github_to_coverage,
        owner=owner,
        repo=repo,
        branch=body.branch,
        token=token,
        owner_id=body.owner_id,
        repo_id=body.repo_id,
        user_name=body.user_name,
        api_key=api_key,
    )
    return {"status": "syncing"}


@app.post(path="/api/{owner}/{repo}/clone_and_install")
async def api_clone_and_install(
    owner: str,
    repo: str,
    api_key: str = Header(..., alias="X-API-Key"),
):
    verify_api_key(api_key)
    return await clone_and_install(owner, repo)


@app.post(path="/api/{owner}/{repo}/setup_coverage_workflow")
async def setup_coverage_workflow(
    owner: str,
    repo: str,
    token: str = Header(..., alias="X-GitHub-Token"),
    api_key: str = Header(..., alias="X-API-Key"),
    sender_id: int = Header(0, alias="X-Sender-Id"),
    sender_name: str = Header("", alias="X-Sender-Name"),
):
    verify_api_key(api_key)
    return await setup_handler(
        owner_name=owner,
        repo_name=repo,
        token=token,
        sender_id=sender_id,
        sender_name=sender_name,
    )
