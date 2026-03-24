from urllib.parse import parse_qs, urlparse

import requests
from bs4 import BeautifulSoup

from config import TIMEOUT
from constants.requests import USER_AGENT
from utils.error.handle_exceptions import handle_exceptions

NUM_RESULTS_DEFAULT = 10

# DuckDuckGo HTML lite endpoint (no JS required, unlike Google which now requires JS)
DDG_URL = "https://html.duckduckgo.com/html/"


@handle_exceptions(default_return_value=[], raise_on_error=False, api_type="web_search")
def search_urls(query: str):
    """Search via DuckDuckGo HTML lite. Google broke all scraping libraries by requiring JS."""
    response = requests.get(
        DDG_URL,
        headers={"User-Agent": USER_AGENT},
        params={"q": query, "kl": "us-en"},  # kl = region/locale
        timeout=TIMEOUT,
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    links = soup.select("a.result__a")
    search_results: list[dict[str, str]] = []
    for link in links[:NUM_RESULTS_DEFAULT]:
        href = str(link.get("href", ""))
        # DDG wraps URLs through a redirect, extract the actual URL
        if "//duckduckgo.com/l/" in href:
            parsed = parse_qs(urlparse(href).query)
            uddg = parsed.get("uddg")
            if uddg:
                href = uddg[0]
        title = link.get_text(strip=True)
        # Get snippet from sibling element
        snippet_tag = link.find_parent("h2")
        description = ""
        if snippet_tag:
            next_div = snippet_tag.find_next_sibling("a", class_="result__snippet")
            if next_div:
                description = next_div.get_text(strip=True)
        search_results.append({"title": title, "description": description, "url": href})

    return search_results
