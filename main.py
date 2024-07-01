# Standard imports
import json
import urllib.parse
from typing import Any

# Third-party imports
import sentry_sdk
from fastapi import FastAPI, HTTPException, Request
from mangum import Mangum
from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration

# Local imports
from config import GITHUB_WEBHOOK_SECRET, ENV, PRODUCT_NAME, UTF8
from scheduler import schedule_handler
from services.github.github_manager import verify_webhook_signature
from services.webhook_handler import handle_webhook_event

if ENV != "local":
    sentry_sdk.init(
        dsn="https://b7ca4effebf7d7825b6464eade11734f@o4506827828101120.ingest.us.sentry.io/4506865231200256",  # noqa
        environment=ENV,
        integrations=[AwsLambdaIntegration()],
        traces_sample_rate=1.0,
    )

# Create FastAPI instance and Mangum handler. Mangum is a library that allows you to use FastAPI with AWS Lambda.
app = FastAPI()
mangum_handler = Mangum(app=app)


# Here is an entry point for the AWS Lambda function. Mangum is a library that allows you to use FastAPI with AWS Lambda.
def handler(event, context):
    print(f"Received event: {event}")
    if "source" in event and event["source"] == "aws.events":
        schedule_handler(event=event, context=context)
        return {"statusCode": 200}

    return mangum_handler(event=event, context=context)


@app.post(path="/webhook")
async def handle_webhook(request: Request) -> dict[str, str]:
    content_type: str = request.headers.get(
        "Content-Type", "Content-Type not specified"
    )
    event_name: str = request.headers.get("X-GitHub-Event", "Event not specified")
    print("\n" * 3 + "-" * 70)
    print(f"Received event: {event_name} with content type: {content_type}")

    # Validate if the webhook signature comes from GitHub
    try:
        print("Webhook received")
        await verify_webhook_signature(request=request, secret=GITHUB_WEBHOOK_SECRET)
        print("Webhook signature verified")
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=401, detail=str(object=e)) from e

    # Process the webhook event but never raise an exception as some event_name like "marketplace_purchase" doesn't have a payload
    try:
        request_body: bytes = await request.body()
    except Exception as e:
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
    except Exception as e:
        print(f"Error in parsing JSON payload: {e}")

    try:
        await handle_webhook_event(event_name=event_name, payload=payload)
        print("Webhook event handled")

        return {"message": "Webhook processed successfully"}
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(object=e)) from e


@app.get(path="/")
async def root() -> dict[str, str]:
    return {"message": PRODUCT_NAME}
