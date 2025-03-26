# Standard imports
import json
import shutil
import tempfile
from typing import Any
import urllib.parse

# Third-party imports
import boto3
from fastapi import FastAPI, Request, BackgroundTasks
from mangum import Mangum
import sentry_sdk
from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration

# Local imports
from config import (
    COVERAGE_QUEUE_URL,
    ENV,
    GITHUB_WEBHOOK_SECRET,
    IS_PRD,
    PRODUCT_NAME,
    SENTRY_DSN,
    UTF8,
)
from scheduler import schedule_handler
from services.git.git_manager import clone_repo
from services.gitauto_handler import handle_gitauto
from services.github.github_manager import (
    verify_webhook_signature,
    get_installation_access_token,
)
from services.github.repo_manager import get_repository_languages
from services.jira.jira_manager import verify_jira_webhook
from services.supabase.coverage_manager import create_or_update_coverages
from services.testing.coverage_analyzer import calculate_test_coverage
from services.webhook_handler import handle_webhook_event
from utils.handle_exceptions import handle_exceptions

if ENV != "local":
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        environment=ENV,
        integrations=[AwsLambdaIntegration()],
        traces_sample_rate=1.0,
    )

# Create FastAPI instance and Mangum handler. Mangum is a library that allows you to use FastAPI with AWS Lambda.
app = FastAPI()
mangum_handler = Mangum(app=app, lifespan="off")

# Create AWS SQS client
sqs = boto3.client("sqs") if IS_PRD else None


# Here is an entry point for the AWS Lambda function. Mangum is a library that allows you to use FastAPI with AWS Lambda.
def handler(event, context):
    print("Entrypoint: handler called")
    print(f"Event: {event}")

    # For coverage calculation request
    if (
        IS_PRD
        and "Records" in event
        and event["Records"][0].get("eventSource") == "aws:sqs"
    ):
        print("Entrypoint: coverage handler called")
        return coverage_handler(json.loads(event["Records"][0]["body"]))

    # For scheduled event
    if "source" in event and event["source"] == "aws.events":
        schedule_handler(_event=event, _context=context)
        return {"statusCode": 200}

    # mangum_handler converts requests from API Gateway to FastAPI routing system
    print("Entrypoint: mangum_handler called")
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
    await handle_gitauto(payload=payload, trigger_type="checkbox", input_from="jira")
    return {"message": "Jira webhook processed successfully"}


@app.get(path="/")
async def root() -> dict[str, str]:
    return {"message": PRODUCT_NAME}


@app.post(path="/coverage")
async def get_repository_coverage(request: Request, background_tasks: BackgroundTasks):
    print("Received request to get repository coverage")
    data = await request.json()

    if IS_PRD:
        print("Sending message to SQS")
        sqs.send_message(QueueUrl=COVERAGE_QUEUE_URL, MessageBody=json.dumps(data))
        print("Message sent to SQS")
        return {"success": True}

    # For local environment
    print("Adding task to background tasks")
    background_tasks.add_task(coverage_handler, data)
    print("Task added to background tasks")
    return {"success": True}


@handle_exceptions(raise_on_error=True)
def coverage_handler(data: dict[str, str | int]):
    print("Starting coverage handler")
    owner_id = data["owner_id"]
    owner_name = data["owner_name"]
    repo_id = data["repo_id"]
    repo_name = data["repo_name"]
    installation_id = data["installation_id"]
    user_name = data["user_name"]

    token = get_installation_access_token(installation_id=installation_id)
    temp_dir = tempfile.mkdtemp()

    try:
        print("Cloning repository")
        clone_repo(owner=owner_name, repo=repo_name, token=token, target_dir=temp_dir)
        print("Cloned repository")

        print("Getting repository languages")
        languages = get_repository_languages(
            owner=owner_name, repo=repo_name, token=token
        )
        print("Got repository languages")

        print("Calculating test coverage")
        coverage = calculate_test_coverage(local_path=temp_dir, languages=languages)
        print("Calculated test coverage")

        print("Creating or updating coverages")
        create_or_update_coverages(
            coverages_list=coverage,
            owner_id=owner_id,
            repo_id=repo_id,
            primary_language=next(iter(languages)),
            user_name=user_name,
        )
        print("Created or updated coverages")
    finally:
        print("Removing temporary directory")
        shutil.rmtree(temp_dir, ignore_errors=True)
        print("Removed temporary directory")

    return {"success": True}
