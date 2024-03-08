# Standard imports
# import json

# Third-party imports
from fastapi import FastAPI, HTTPException, Request
from mangum import Mangum
import sentry_sdk
from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration

# Local imports
from config import GITHUB_WEBHOOK_SECRET, ENV
from services.github.github_manager import verify_webhook_signature
from services.webhook_handler import handle_webhook_event

from testing import apply_patch, original_text, diff

# Create FastAPI instance
app = FastAPI()

sentry_sdk.init(
    "https://b7ca4effebf7d7825b6464eade11734f@o4506827828101120.ingest.us.sentry.io/4506865231200256",
    environment=ENV,
    integrations=[AwsLambdaIntegration()],
    traces_sample_rate=1.0
)
@app.get('/test')
def test():
    apply_patch(original_text, diff)
    return {"message": original_text}

@app.get("/sentry-debug")
def read_health_check():
    division_by_zero = 1/0
    return {"version": "1.0.0"}

handler = Mangum(app=app)

@app.post(path="/webhook")
async def handle_webhook(request: Request) -> dict[str, str]:
    try:
        print("Webhook received")
        # Validate the webhook signature
        await verify_webhook_signature(request=request, secret=GITHUB_WEBHOOK_SECRET)
        print("Webhook signature verified")

        # Process the webhook event
        payload = await request.json()
        # formatted_payload: str = json.dumps(obj=payload, indent=4)
        # print(f"Payload: {formatted_payload}")

        # TODO: Sanitize the payload to remove any sensitive information
        # Handle Create, Delete, and Labeled events
        await handle_webhook_event(payload=payload)
        print("Webhook event handled")

        return {"message": "Webhook processed successfully"}
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(object=e)) from e


@app.get(path="/")
async def root():
    return {"message": "PR Agent APP"}
