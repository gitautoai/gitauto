# Standard imports
import json

# Third-party imports
from fastapi import FastAPI, HTTPException, Request
import urllib.parse

# Local imports
from .services.github.github_manager import GitHubManager
from .services.github.webhook_handler import handle_webhook_event
from config import GITHUB_APP_ID, GITHUB_PRIVATE_KEY, GITHUB_WEBHOOK_SECRET

from mangum import Mangum
app = FastAPI()
handler = Mangum(app=app)

github_manager = GitHubManager(GITHUB_APP_ID, GITHUB_PRIVATE_KEY)


@app.post("/webhook")
async def handle_webhook(request: Request):
    try:
        print("Webhook received")
        payload = await request.body()
        decoded_data = urllib.parse.unquote(payload.decode())
        json_data = json.loads(decoded_data)

        # Handle Create, Delete, and Labeled events
        await handle_webhook_event(json_data)
        print("Webhook event handled")

        return {"message": "Webhook processed successfully"}
    except Exception as e:
        print(f"Error: {e}")        
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/yo")
async def root():
    return {"message": "Hello World"}

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)

