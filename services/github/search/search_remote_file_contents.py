import requests

from config import GITHUB_API_URL, TIMEOUT
from services.github.types.github_types import BaseArgs
from services.github.utils.create_headers import create_headers
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value="", raise_on_error=False)
def search_remote_file_contents(query: str, base_args: BaseArgs, **_kwargs) -> str:
    """
    - Only the default branch is considered.
    - Only files smaller than 384 KB are searchable.
    - This endpoint requires you to authenticate and limits you to 10 requests per minute.

    https://docs.github.com/en/rest/search/search?apiVersion=2022-11-28
    https://docs.github.com/en/search-github/getting-started-with-searching-on-github/understanding-the-search-syntax
    https://docs.github.com/en/search-github/searching-on-github/searching-in-forks
    """
    owner, repo, is_fork, token = (
        base_args["owner"],
        base_args["repo"],
        base_args["is_fork"],
        base_args["token"],
    )
    q = f"{query} repo:{owner}/{repo}"
    if is_fork:
        q = f"{query} repo:{owner}/{repo} fork:true"
    params = {"q": q, "per_page": 10, "page": 1}  # per_page: max 100
    url = f"{GITHUB_API_URL}/search/code"
    headers: dict[str, str] = create_headers(token=token)
    headers["Accept"] = "application/vnd.github.text-match+json"
    response = requests.get(url=url, headers=headers, params=params, timeout=TIMEOUT)
    response.raise_for_status()
    response_json = response.json()
    file_paths = []
    for item in response_json.get("items", []):
        file_path = item["path"]
        file_paths.append(file_path)
    msg = (
        f"{len(file_paths)} files found for the search query '{query}':\n- "
        + "\n- ".join(file_paths)
        + "\n"
    )
    print(msg)
    return msg
