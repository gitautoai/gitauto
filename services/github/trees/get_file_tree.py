import requests
from config import GITHUB_API_URL, TIMEOUT
from services.github.types.github_types import BaseArgs
from services.github.utils.create_headers import create_headers
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=[], raise_on_error=False)
def get_file_tree(base_args: BaseArgs, max_files: int = 100):
    """
    Get the file tree of a GitHub repository at a ref branch.
    Uses recursive API call and trims results from deepest level if exceeding max_files.
    https://docs.github.com/en/rest/git/trees?apiVersion=2022-11-28#get-a-tree
    """
    owner, repo, ref = base_args["owner"], base_args["repo"], base_args["base_branch"]

    # Get complete tree recursively
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/git/trees/{ref}"
    headers: dict[str, str] = create_headers(token=base_args["token"])
    params: dict[str, int | str] = {"recursive": 1}
    response = requests.get(url=url, headers=headers, params=params, timeout=TIMEOUT)

    # Handle empty repository case
    if response.status_code == 409 and "Git Repository is empty" in response.text:
        print(f"Repository {owner}/{repo} is empty")
        return [], "Repository is empty."

    # Handle 404 error case (repository or branch not found)
    if response.status_code == 404:
        print(f"No files found in repository: {owner}/{repo}")
        return [], "No files found in repository."

    response.raise_for_status()

    # Warn if GitHub API truncated the response
    if response.json().get("truncated"):
        print("Warning: Repository tree was truncated by GitHub API")

    # Group files by their depth
    paths_by_depth: dict[int, list[str]] = {}
    for item in response.json()["tree"]:
        if item["type"] != "blob":  # Skip non-file items
            continue
        path = item["path"]
        depth = path.count("/")
        paths_by_depth.setdefault(depth, []).append(path)

    # Collect files starting from shallowest depth
    result: list[str] = []
    max_depth = max(paths_by_depth.keys()) if paths_by_depth else 0

    for depth in range(max_depth + 1):
        if depth in paths_by_depth:
            result.extend(sorted(paths_by_depth[depth]))

    total_files = len(result)
    if max_files and total_files > max_files:
        result = result[:max_files]
        msg = f"Found {total_files} files across {max_depth + 1} directory levels but limited to {max_files} files for now."
    else:
        msg = f"Found {total_files} files across {max_depth + 1} directory levels."

    # Sort the result by alphabetical order
    result.sort()

    return result, msg
