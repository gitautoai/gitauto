# Standard imports
import json

# Third-party imports
from fastapi import FastAPI, HTTPException, Request
from mangum import Mangum

# Local imports
from config import GITHUB_APP_ID, GITHUB_PRIVATE_KEY, GITHUB_WEBHOOK_SECRET
from services.github.github_manager import GitHubManager
from services.github.webhook_handler import handle_webhook_event

# Create FastAPI instance
app = FastAPI()
handler = Mangum(app=app)

# Initialize GitHub manager
github_manager = GitHubManager(app_id=GITHUB_APP_ID, private_key=GITHUB_PRIVATE_KEY)


@app.post(path="/webhook")
async def handle_webhook(request: Request) -> dict[str, str]:
    try:
        print("Webhook received")
        # Validate the webhook signature
        # await github_manager.verify_webhook_signature(request=request, secret=GITHUB_WEBHOOK_SECRET)
        print("Webhook signature verified")

        # Process the webhook event
        payload = await request.json()
        formatted_payload: str = json.dumps(obj=payload, indent=4)
        print(f"Payload: {formatted_payload}")

        # TODO: Sanitize the payload to remove any sensitive information
        # Handle Create, Delete, and Labeled events
        await handle_webhook_event(payload=payload)
        print("Webhook event handled")

        return {"message": "Webhook processed successfully"}
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(object=e))

@app.get(path="/")
async def root():
    return {"message": "PR Agent APP"}


