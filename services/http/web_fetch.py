import html2text
import requests
from anthropic.types import ToolUnionParam
from bs4 import BeautifulSoup

from config import TIMEOUT
from constants.models import ClaudeModelId
from constants.requests import USER_AGENT
from services.claude.chat_with_claude_simple import chat_with_claude_simple
from services.http.github_auth_headers import github_auth_headers
from services.slack.slack_notify import slack_notify
from services.types.base_args import BaseArgs
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger

UNNECESSARY_TAGS = [
    "ads",
    "advertisement",
    "aside",
    "footer",
    "head",
    "header",
    "iframe",
    "link",
    "meta",
    "nav",
    "noscript",
    "path",
    "script",
    "style",
    "svg",
]

WEB_FETCH: ToolUnionParam = {
    "name": "web_fetch",
    "description": "Fetch a webpage, extract relevant information using a prompt, and return a summary. Use this to read documentation, API references, or any URL relevant to the task. Only fetch URLs that are relevant to the task.",
    "input_schema": {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "The full URL to fetch content from (must start with https://).",
            },
            "prompt": {
                "type": "string",
                "description": "What information to extract from the page. Be specific about what you need.",
            },
        },
        "required": ["url", "prompt"],
        "additionalProperties": False,
    },
    "strict": True,
}


@handle_exceptions(default_return_value=None, raise_on_error=False)
def web_fetch(base_args: BaseArgs, url: str, prompt: str, **_kwargs):
    owner = base_args.get("owner", "unknown")
    repo = base_args.get("repo", "unknown")
    logger.info("Fetching URL: url=%s, owner=%s, repo=%s", url, owner, repo)

    # raw.githubusercontent.com and api.github.com return 404 for private repos without a token (AGENT-364/363/23G). Send the installation token so fetching the agent's own private repo content works; harmless for other URLs.
    headers = {"User-Agent": USER_AGENT}
    headers.update(github_auth_headers(url, base_args.get("token")))
    response = requests.get(url, headers=headers, timeout=TIMEOUT)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Get title before removing unnecessary elements
    title = soup.title.string if soup.title else ""

    # Remove unnecessary elements
    for element in soup.select(", ".join(UNNECESSARY_TAGS)):
        element.decompose()

    logger.info("Scraped url: %s, Title: %s", url, title)

    # Find main content area if possible
    main_content = soup.select_one("main, article, div[role='main']") or soup

    # Convert HTML to markdown so Claude can parse headings, code blocks, links, etc.
    converter = html2text.HTML2Text()
    converter.ignore_images = True
    converter.body_width = 0  # No line wrapping
    markdown = converter.handle(str(main_content)).strip()

    # Summarize using Haiku to avoid sending full page content to the main (expensive) model
    usage_id = base_args.get("usage_id", 0)
    summary = chat_with_claude_simple(
        system_input=f"You are extracting information from a web page at {url} (title: {title}).",
        user_input=f"{markdown}\n\n---\n\n{prompt}",
        usage_id=usage_id,
        model_id=ClaudeModelId.HAIKU_4_5,
    )

    result = {
        "title": title.strip() if title else "",
        "content": summary,
        "url": url,
    }
    thread_ts = base_args.get("slack_thread_ts")
    slack_notify(
        f"🌐 Fetched URL in `{owner}/{repo}`:\n"
        f"URL: `{url}`\n"
        f"Success: {result is not None}",
        thread_ts,
    )
    logger.info("web_fetch returning result for %s", url)
    return result
