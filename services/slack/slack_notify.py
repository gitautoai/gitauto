# Standard imports
import os

# Third party imports
import requests

# Local imports
from config import TIMEOUT
from constants.slack import SLACK_CHANNEL_ID
from constants.general import IS_PRD
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")


@handle_exceptions(default_return_value=None, raise_on_error=False)
def slack_notify(text: str, thread_ts: str | None = None):
    if not IS_PRD:
        logger.info("slack_notify: skipping non-prod environment")
        return None
    if not SLACK_BOT_TOKEN:
        logger.error("slack_notify: SLACK_BOT_TOKEN is not set")
        raise ValueError("SLACK_BOT_TOKEN is not set")

    headers = {
        "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {"channel": SLACK_CHANNEL_ID, "text": text}

    if thread_ts:
        logger.info("slack_notify: posting in thread %s", thread_ts)
        payload["thread_ts"] = thread_ts

    response = requests.post(
        "https://slack.com/api/chat.postMessage",
        headers=headers,
        json=payload,
        timeout=TIMEOUT,
    )

    if response.status_code != 200:
        logger.error(
            "Slack notification failed: %s %s", response.status_code, response.text
        )
        return None

    response_data = response.json()
    if not response_data.get("ok"):
        logger.error("Slack notification failed: %s", response_data.get("error"))
        return None

    ts: str = response_data.get("ts")
    logger.info("slack_notify: posted ts=%s", ts)
    return ts
