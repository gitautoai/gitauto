from bs4 import BeautifulSoup
from googlesearch import search
from requests import get
import logging
from config import TIMEOUT
from constants.requests import USER_AGENT
from services.github.github_types import BaseArgs
from utils.handle_exceptions import handle_exceptions

logger = logging.getLogger(__name__)
NUM_RESULTS_DEFAULT = 1
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

DEFAULT_RATE_LIMIT = 1000

@handle_exceptions(default_return_value=[], raise_on_error=False)
def search_urls(query: str, num_results: int = NUM_RESULTS_DEFAULT, lang: str = "en"):
    """https://pypi.org/project/googlesearch-python/"""
    search_results: list[dict[str, str]] = []
    results = search(
        term=query, num_results=num_results, lang=lang, safe=None, advanced=True
    )
    for result in results:
        title = result.title
        description = result.description
        url = result.url
        search_results.append({"title": title, "description": description, "url": url})

    return search_results


@handle_exceptions(default_return_value=None, raise_on_error=False)
def scrape_content_from_url(url: str):
    headers = {"User-Agent": USER_AGENT}
    response = get(url, headers=headers, timeout=TIMEOUT)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Remove unnecessary elements
    for element in soup(UNNECESSARY_TAGS):
        element.decompose()

    # Get title and content
    title = soup.title.string if soup.title else ""
    print(f"Googled url: {url}\nTitle: {title}")

    # Print unique HTML tags
    unique_tags = set(tag.name for tag in soup.find_all())
    print(f"Unique HTML tags found: {sorted(unique_tags)}")

    # Find main content area if possible
    main_content = soup.find(["main", "article", 'div[role="main"]']) or soup
    content = "\n".join(main_content.stripped_strings).strip()

    return {"title": title.strip(), "content": content, "url": url}


@handle_exceptions(default_return_value=[], raise_on_error=False)
def google_search(
    base_args: BaseArgs,
    query: str,
    num_results: int = NUM_RESULTS_DEFAULT,
    lang: str = "en",
):
    urls = search_urls(query=query, num_results=num_results, lang=lang)
    contents = []
    for url in urls:
        contents.append(scrape_content_from_url(url["url"]))
        # Example of accessing headers (assuming response is available)
        # response = some_function_to_get_response()
        # rate_limit = response.headers.get('x-ratelimit-limit', DEFAULT_RATE_LIMIT)
        # if 'x-ratelimit-limit' not in response.headers:
        #     logger.warning("Missing 'x-ratelimit-limit' header in Google API response.")

    return contents
