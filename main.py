# Standard imports
# import json

# Third-party imports
from fastapi import FastAPI, HTTPException, Request
from mangum import Mangum
import sentry_sdk
from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration
import pprint

# Local imports
from config import GH_WEBHOOK_SECRET, ENV, PRODUCT_NAME
from services.github.github_manager import verify_webhook_signature
from services.webhook_handler import handle_webhook_event

# Create FastAPI instance
app = FastAPI()

if ENV != "local":
    sentry_sdk.init(
        dsn="https://b7ca4effebf7d7825b6464eade11734f@o4506827828101120.ingest.us.sentry.io/4506865231200256",  # noqa
        environment=ENV,
        integrations=[AwsLambdaIntegration()],
        traces_sample_rate=1.0,
    )

handler = Mangum(app=app)


@app.post(path="/webhook")
async def handle_webhook(request: Request) -> dict[str, str]:
    event_name: str = request.headers.get("X-GitHub-Event", "Event not specified")
    print(f"Received event: {event_name}")

    try:
        print("Webhook received")
        # Validate the webhook signature
        await verify_webhook_signature(request=request, secret=GH_WEBHOOK_SECRET)
        print("Webhook signature verified")

        # Process the webhook event
        payload = await request.json()
        # pprint.PrettyPrinter(indent=4).pprint(payload)

        await handle_webhook_event(event_name=event_name, payload=payload)
        print("Webhook event handled")

        return {"message": "Webhook processed successfully"}
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(object=e)) from e


@app.get(path="/")
async def root() -> dict[str, str]:
    return {"message": PRODUCT_NAME}
