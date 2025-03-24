# Standard imports
import json
import urllib.parse
import shutil
import tempfile
from typing import Any

# Third-party imports
import sentry_sdk
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from mangum import Mangum
from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration

# Local imports
from config import GITHUB_WEBHOOK_SECRET, ENV, PRODUCT_NAME, SENTRY_DSN, UTF8
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


# Here is an entry point for the AWS Lambda function. Mangum is a library that allows you to use FastAPI with AWS Lambda.
def handler(event, context):
    if "source" in event and event["source"] == "aws.events":
        schedule_handler(_event=event, _context=context)
        return {"statusCode": 200}

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


@app.post(path="/api/repository/coverage")
async def get_repository_coverage(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()
    owner_id = data.get("owner_id")
    owner_name = data.get("owner_name")
    repo_id = data.get("repo_id")
    repo_name = data.get("repo_name")
    installation_id = data.get("installation_id")
    user_name = data.get("user_name")

    if not all([owner_name, repo_name, installation_id]):
        raise HTTPException(status_code=400, detail="Missing required parameters")

    # Start background task
    background_tasks.add_task(
        process_coverage_task,
        owner_id=owner_id,
        owner_name=owner_name,
        repo_id=repo_id,
        repo_name=repo_name,
        installation_id=installation_id,
        user_name=user_name,
    )

    return {"success": True}


async def process_coverage_task(
    owner_id: int,
    owner_name: str,
    repo_id: int,
    repo_name: str,
    installation_id: int,
    user_name: str,
):
    token = get_installation_access_token(installation_id=installation_id)
    if not token:
        raise HTTPException(status_code=401, detail="Failed to get installation token")
    temp_dir = tempfile.mkdtemp()
    try:
        clone_repo(owner=owner_name, repo=repo_name, token=token, target_dir=temp_dir)
        languages = get_repository_languages(
            owner=owner_name, repo=repo_name, token=token
        )
        coverage = calculate_test_coverage(local_path=temp_dir, languages=languages)
        create_or_update_coverages(
            coverages_list=coverage,
            owner_id=owner_id,
            repo_id=repo_id,
            primary_language=next(iter(languages)),
            user_name=user_name,
        )
    except Exception as e:  # pylint: disable=broad-except
        raise HTTPException(status_code=500, detail=str(e)) from e
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
