import requests
from anthropic.types import ToolUnionParam

from config import TIMEOUT
from constants.requests import USER_AGENT
from services.http.github_auth_headers import github_auth_headers
from services.http.is_html import is_html
from services.http.strip_html import strip_html
from services.slack.slack_notify import slack_notify
from services.types.base_args import BaseArgs
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger

# Raw curl output stays in conversation history for every subsequent LLM call. HTML pages with CSS/JS can be 100K+ chars, costing $0.30+ per call × 40+ calls = $12+ wasted.
MAX_CURL_CHARS = 10_000

CURL: ToolUnionParam = {
    "name": "curl",
    "description": "Fetch raw content from a URL. Best for JSON APIs and raw text. For HTML pages, use web_fetch instead — curl truncates HTML responses to avoid excessive token usage.",
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

    # api.github.com returns 404 for private repos without a token (AGENT-35Y/35X).
    # Send the installation token so fetching private repo content works; harmless otherwise.
    headers = {"User-Agent": USER_AGENT}
    headers.update(github_auth_headers(url, base_args.get("token")))
    response = requests.get(url, headers=headers, timeout=TIMEOUT)
    response.raise_for_status()

    raw_len = len(response.text)
    html_detected = is_html(response)

    if html_detected:
        logger.info("Curl: HTML detected, stripping tags")
        content = strip_html(response.text)
        logger.info("Curl: stripped HTML tags: %d -> %d chars", raw_len, len(content))
    else:
        logger.info("Curl: non-HTML response, raw=%d chars", raw_len)
        content = response.text

    truncated = False
    if len(content) > MAX_CURL_CHARS:
        logger.info("Curl: truncating from %d to %d chars", raw_len, MAX_CURL_CHARS)
        content = content[:MAX_CURL_CHARS]
        truncated = True

    suffix = ""
    if truncated:
        logger.info("Curl: appending truncation suffix")
        suffix = f"\n\n[Truncated from {raw_len:,} to {MAX_CURL_CHARS:,} chars. Use web_fetch for full HTML page summarization.]"
    if html_detected:
        logger.info("Curl: appending HTML suffix")
        suffix = f"\n\n[HTML page detected — tags stripped. For better results, use web_fetch instead.]{suffix}"

    logger.info("Curl completed: url=%s, raw=%d, final=%d", url, raw_len, len(content))

    thread_ts = base_args.get("slack_thread_ts")
    slack_notify(f"🌐 Curl: `{url}` ({raw_len} raw, {len(content)} final)", thread_ts)
    logger.info("Curl returning %d chars for %s", len(content + suffix), url)
    return content + suffix
