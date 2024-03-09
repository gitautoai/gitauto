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
from utils.file_manager import apply_patch
# Create FastAPI instance
app = FastAPI()

original_text = """import type { NextApiRequest, NextApiResponse } from "next";

import { z, ZodError } from "zod";

const schema = z.object({
  folderName: z.string(),
});

import { v2 as cloudinary } from "cloudinary";

cloudinary.config({
  cloud_name: "duaiiecow",
  api_key: "896513553396748",
  api_secret: "dtVnFQqHwz1WsYSUN3w52n6rqWs",
});

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method !== "GET") {
    res.status(405).json({ message: "Method not allowed" });
    return;
  }

  try {
    const folderName = schema.parse(req.query).folderName;

    const images = await cloudinary.api.resources({
      type: "upload",
      prefix: folderName,
      max_results: 100,
    });
    const videos = await cloudinary.api.resources({
      type: "upload",
      resource_type: "video",
      prefix: folderName,
      max_results: 100,
    });

    let imageAssets = images.resources.map((resource: any) => ({
      public_id: resource.public_id,
      url: resource.secure_url,
    }));

    let videoAssets = videos.resources.map((resource: any) => ({
      public_id: resource.public_id,
      url: resource.secure_url,
    }));

    res
      .status(200)
      .json({ imageAssets: imageAssets, videoAssets: videoAssets });
  } catch (err) {
    console.error(err);
    if (err instanceof ZodError) {
      res.status(400).json({ message: err.issues[0].message });
    } else {
      res.status(500).json({ message: "Internal server error" });
    }
  }
  return;
}"""
sentry_sdk.init(
    "https://b7ca4effebf7d7825b6464eade11734f@o4506827828101120.ingest.us.sentry.io/4506865231200256",
    environment=ENV,
    integrations=[AwsLambdaIntegration()],
    traces_sample_rate=1.0
)

handler = Mangum(app=app)

@app.get(path="/test")
async def test():
    apply_patch(original_text="Hello", diff_text="World")
    return {"message": "Test successful"}

@app.get(path="/test2")
async def test():
    diff_text = """```diff
--- pages/api/photos/get-cloudinary-photos.ts
+++ pages/api/photos/get-cloudinary-photos.ts
@@ -0,0 +1,22 @@
+import type { NextApiRequest, NextApiResponse } from 'next';
+import { v2 as cloudinary } from 'cloudinary';
+
+export default async function handler(
+  req: NextApiRequest,
+  res: NextApiResponse
+) {
+  cloudinary.config({
+    cloud_name: process.env.CLOUDINARY_CLOUD_NAME,
+    api_key: process.env.CLOUDINARY_API_KEY,
+    api_secret: process.env.CLOUDINARY_API_SECRET,
+  });
+
+  const { resources } = await cloudinary.search
+    .expression('folder:merch')
+    .sort_by('public_id', 'desc')
+    .max_results(30)
+    .execute();
+
+  const images = resources.map(({ public_id, secure_url }) => ({ public_id, url: secure_url }));
+  res.status(200).json({ images });
+}
```"""
    apply_patch(original_text=original_text, diff_text=diff_text)
    return {"message": "Test successful"}

@app.get(path="/test3")
async def test():
    diff_text = """
--- pages/api/photos/get-cloudinary-photos.ts
+++ pages/api/photos/get-cloudinary-photos.ts
@@ -0,0 +1,22 @@
+import type { NextApiRequest, NextApiResponse } from 'next';
+import { v2 as cloudinary } from 'cloudinary';
+
+export default async function handler(
+  req: NextApiRequest,
+  res: NextApiResponse
+) {
+  cloudinary.config({
+    cloud_name: process.env.CLOUDINARY_CLOUD_NAME,
+    api_key: process.env.CLOUDINARY_API_KEY,
+    api_secret: process.env.CLOUDINARY_API_SECRET,
+  });
+
+  const { resources } = await cloudinary.search
+    .expression('folder:merch')
+    .sort_by('public_id', 'desc')
+    .max_results(30)
+    .execute();
+
+  const images = resources.map(({ public_id, secure_url }) => ({ public_id, url: secure_url }));
+  res.status(200).json({ images });
+}
"""
    apply_patch(original_text=original_text, diff_text=diff_text)
    return {"message": "Test successful"}

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
