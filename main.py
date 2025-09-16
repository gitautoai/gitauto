# Standard imports
import json
from typing import Any, cast
import urllib.parse

# Third-party imports
from fastapi import FastAPI, Request
from mangum import Mangum
import sentry_sdk
from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration

# Local imports
from config import ENV, GITHUB_WEBHOOK_SECRET, PRODUCT_NAME, SENTRY_DSN, UTF8
from payloads.aws.event_bridge_scheduler.event_types import EventBridgeSchedulerEvent
from services.github.utils.verify_webhook_signature import verify_webhook_signature
from services.jira.verify_jira_webhook import verify_jira_webhook
from services.slack.slack_notify import slack_notify
from services.webhook.issue_handler import create_pr_from_issue
from services.webhook.schedule_handler import schedule_handler
from services.webhook.webhook_handler import handle_webhook_event
from utils.aws.extract_lambda_info import extract_lambda_info

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
    # For scheduled event from EventBridge Scheduler
    if "triggerType" in event and event["triggerType"] == "schedule":
        print("AWS EventBridge Scheduler invoked")
        event = cast(EventBridgeSchedulerEvent, event)
        owner_name = event.get("ownerName", "")
        repo_name = event.get("repoName", "")
        thread_ts = slack_notify(
            f"Event Scheduler started for {owner_name}/{repo_name}"
        )

        result = schedule_handler(event=event)
        if result["status"] == "success":
            slack_notify("Completed", thread_ts)
        else:
            slack_notify(
                f"@channel Failed: {result['message']}",
                thread_ts,
            )
        return None

    # mangum_handler converts requests from API Gateway to FastAPI routing system
    return mangum_handler(event=event, context=context)


@app.post(path="/webhook")
async def handle_webhook(request: Request) -> dict[str, str]:
    event_name: str = request.headers.get("X-GitHub-Event", "Event not specified")

    # Extract Lambda context information if available
    lambda_info = extract_lambda_info(request)

    # Validate if the webhook signature comes from GitHub
    await verify_webhook_signature(request=request, secret=GITHUB_WEBHOOK_SECRET)

    # Process the webhook event but never raise an exception as some event_name like "marketplace_purchase" doesn't have a payload
    try:
        request_body: bytes = await request.body()
    except Exception as e:  # pylint: disable=broad-except
        print(f"Error in reading request body: {e}")
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
                pass  # Keep payload as empty dict
    except Exception as e:  # pylint: disable=broad-except
        print(f"Error in parsing JSON payload: {e}")

    await handle_webhook_event(
        event_name=event_name, payload=payload, lambda_info=lambda_info
    )
    return {"message": "Webhook processed successfully"}


@app.post(path="/jira-webhook")
async def handle_jira_webhook(request: Request):
    # Extract Lambda context information if available
    lambda_info = extract_lambda_info(request)

    payload = await verify_jira_webhook(request)
    create_pr_from_issue(
        payload=payload,
        trigger="issue_comment",
        input_from="jira",
        lambda_info=lambda_info,
    )
    return {"message": "Jira webhook processed successfully"}


@app.get(path="/")
async def root() -> dict[str, str]:
    return {"message": PRODUCT_NAME}
