import json

from fastapi import FastAPI, HTTPException, Request
import urllib.parse

from services.github.webhook_handler import handle_webhook_event

from mangum import Mangum
app = FastAPI()
handler = Mangum(app=app)


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

