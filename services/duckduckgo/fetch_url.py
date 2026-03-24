import html2text
import requests
from anthropic.types import ToolUnionParam
from bs4 import BeautifulSoup

from config import TIMEOUT
from constants.requests import USER_AGENT
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

FETCH_URL: ToolUnionParam = {
    "name": "fetch_url",
    "description": "Fetch a webpage and return its content as markdown. Use this after search_web to read the full content of a specific URL from the search results. Only fetch URLs that are relevant to the task.",
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


@handle_exceptions(
    default_return_value=None, raise_on_error=False, api_type="web_search"
)
def fetch_url(base_args: BaseArgs, url: str, **_kwargs):
    owner = base_args.get("owner", "unknown")
    repo = base_args.get("repo", "unknown")
    logger.info("Fetching URL: url=%s, owner=%s, repo=%s", url, owner, repo)

    headers = {"User-Agent": USER_AGENT}
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
    content = converter.handle(str(main_content)).strip()

    result = {"title": title.strip() if title else "", "content": content, "url": url}
    slack_notify(
        f"🌐 Fetched URL in `{owner}/{repo}`:\n"
        f"URL: `{url}`\n"
        f"Success: {result is not None}"
    )
    return result
