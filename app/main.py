# Standard imports
import json

# Third-party imports
from fastapi import FastAPI, HTTPException, Request

# Local imports
from .services.github.github_manager import GitHubManager
from .services.github.webhook_handler import handle_webhook_event
from config import GITHUB_APP_ID, GITHUB_PRIVATE_KEY, GITHUB_WEBHOOK_SECRET

# Create FastAPI instance
app = FastAPI()

# Initialize GitHub manager
github_manager = GitHubManager(GITHUB_APP_ID, GITHUB_PRIVATE_KEY)


@app.post("/webhook")
async def handle_webhook(request: Request):
    try:
        print("Webhook received")
        # Don't think a secret will be necessary, unless we can hide it from end users
        # await github_manager.verify_webhook_signature(request, GITHUB_WEBHOOK_SECRET)

        # Process the webhook event
        webhook_payload = await request.body()
        print("PAYLOAD: ", webhook_payload)
        formatted_payload = json.dumps(webhook_payload, indent=4)
        print(f"Payload: {formatted_payload}")

        # Handle Create, Delete, and Labeled events
        await handle_webhook_event(webhook_payload)
        print("Webhook event handled")

        return {"message": "Webhook processed successfully"}
    except Exception as e:
        print(f"Error: {e}")        
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

