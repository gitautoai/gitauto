# Standard imports
import os

# Third party imports
import requests

# Local imports
from config import TIMEOUT
from constants.general import IS_PRD
from utils.error.handle_exceptions import handle_exceptions

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")


@handle_exceptions(default_return_value=None, raise_on_error=False)
def slack_notify(text: str, thread_ts: str | None = None):
    if not IS_PRD:
        print("Skipping Slack notification in non-production environment")
        return None
    if not SLACK_BOT_TOKEN:
        raise ValueError("SLACK_BOT_TOKEN is not set")

    headers = {
        "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {"channel": "C08PHH352S3", "text": text}

    if thread_ts:
        payload["thread_ts"] = thread_ts

    response = requests.post(
        "https://slack.com/api/chat.postMessage",
        headers=headers,
        json=payload,
        timeout=TIMEOUT,
    )

    if response.status_code != 200:
        print(f"Slack notification failed: {response.status_code} {response.text}")
        return None

    response_data = response.json()
    if not response_data.get("ok"):
        print(f"Slack notification failed: {response_data.get('error')}")
        return None

    ts: str = response_data.get("ts")
    return ts
