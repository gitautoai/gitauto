# Standard imports
import json
from typing import Any
import urllib.parse

# Third-party imports
from fastapi import FastAPI, Request
from mangum import Mangum
import sentry_sdk
from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration

# Local imports
from config import ENV, GITHUB_WEBHOOK_SECRET, PRODUCT_NAME, SENTRY_DSN, UTF8
from services.github.github_manager import verify_webhook_signature
from services.jira.jira_manager import verify_jira_webhook
from services.slack.slack_notify import slack_notify
from services.webhook.issue_handler import create_pr_from_issue
from services.webhook.schedule_handler import schedule_handler
from services.webhook.webhook_handler import handle_webhook_event

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
    print("event: ", event)
    print("context: ", context)

    # For scheduled event
    if "source" in event and event["source"] in ["aws.events", "aws.scheduler"]:
        detail = event.get("detail", {})
        owner_name = detail.get("ownerName", "")
        repo_name = detail.get("repoName", "")
        thread_ts = slack_notify(
            f"Event Scheduler started for {owner_name}/{repo_name}"
        )

        result = schedule_handler(event=event, _context=context)
        if result["status"] == "success":
            slack_notify("Completed", thread_ts)
        else:
            slack_notify(
                f"@channel Failed: {result['message']}",
                thread_ts,
            )
        return

    # mangum_handler converts requests from API Gateway to FastAPI routing system
    return mangum_handler(event=event, context=context)


@app.post(path="/webhook")
async def handle_webhook(request: Request) -> dict[str, str]:
    event_name: str = request.headers.get("X-GitHub-Event", "Event not specified")

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
            payload = json.loads(s=decoded_body["payload"][0])
    except Exception as e:  # pylint: disable=broad-except
        print(f"Error in parsing JSON payload: {e}")

    await handle_webhook_event(event_name=event_name, payload=payload)
    return {"message": "Webhook processed successfully"}


@app.post(path="/jira-webhook")
async def handle_jira_webhook(request: Request):
    payload = await verify_jira_webhook(request)
    await create_pr_from_issue(
        payload=payload, trigger_type="checkbox", input_from="jira"
    )
    return {"message": "Jira webhook processed successfully"}


@app.get(path="/")
async def root() -> dict[str, str]:
    return {"message": PRODUCT_NAME}
