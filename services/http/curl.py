import requests
from anthropic.types import ToolUnionParam

from config import TIMEOUT
from constants.requests import USER_AGENT
from services.slack.slack_notify import slack_notify
from services.types.base_args import BaseArgs
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger

CURL: ToolUnionParam = {
    "name": "curl",
    "description": "Fetch raw content from a URL. Use for JSON APIs, raw text files, or when you need exact unprocessed content. Unlike web_fetch, this returns the raw response body without HTML parsing or summarization.",
    "input_schema": {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "The full URL to fetch content from (must start with https://).",
            },
        },
        "required": ["url"],
        "additionalProperties": False,
    },
    "strict": True,
}


@handle_exceptions(default_return_value=None, raise_on_error=False)
def curl(base_args: BaseArgs, url: str, **_kwargs):
    logger.info("Curl URL: url=%s", url)

    headers = {"User-Agent": USER_AGENT}
    response = requests.get(url, headers=headers, timeout=TIMEOUT)
    response.raise_for_status()

    content = response.text
    logger.info("Curl completed: url=%s, length=%d", url, len(content))

    thread_ts = base_args.get("slack_thread_ts")
    slack_notify(f"🌐 Curl: `{url}` ({len(content)} chars)", thread_ts)
    return content
