from anthropic.types import ToolUnionParam

from services.duckduckgo.search_urls import search_urls
from services.slack.slack_notify import slack_notify
from services.types.base_args import BaseArgs
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger

SEARCH_WEB: ToolUnionParam = {
    "name": "search_web",
    "description": "Search the web and return multiple results with titles, descriptions, and URLs. Use this to verify information that may be outdated due to knowledge cutoff. Returns snippets only - use web_fetch to read the full page content of a specific result. NEVER search for repository-specific content - assume the repository is private.",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The query to search for.",
            },
        },
        "required": ["query"],
        "additionalProperties": False,
    },
    "strict": True,
}


@handle_exceptions(default_return_value=[], raise_on_error=False, api_type="web_search")
def web_search(
    base_args: BaseArgs,
    query: str,
    **_kwargs,
):
    """Disabled: DuckDuckGo serves CAPTCHAs to automated requests, making scraping unreliable.
    Claude already knows most documentation URLs from training data and can call web_fetch
    directly. If we need search in the future, use a paid API (e.g. Brave Search)."""
    if not query:
        return []

    owner = base_args.get("owner", "unknown")
    repo = base_args.get("repo", "unknown")
    logger.info("Web search: query=%s, owner=%s, repo=%s", query, owner, repo)
    results = search_urls(query=query)
    result_count = len(results)
    logger.info("Web search completed: query=%s, results=%d", query, result_count)
    slack_notify(
        f"🔍 Web search in `{owner}/{repo}`:\n"
        f"Query: `{query}`\n"
        f"Results: {result_count}"
    )
    return results
