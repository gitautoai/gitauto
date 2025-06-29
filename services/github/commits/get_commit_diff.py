# Third party imports
import requests

# Local imports
from config import GITHUB_API_URL, TIMEOUT
from services.github.utils.create_headers import create_headers
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def get_commit_diff(owner: str, repo: str, commit_sha: str, token: str) -> dict | None:
    """
    Get commit diff from GitHub API.
    https://docs.github.com/en/rest/commits/commits#get-a-commit
    """
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/commits/{commit_sha}"
    headers = create_headers(token=token)

    response = requests.get(url=url, headers=headers, timeout=TIMEOUT)
    response.raise_for_status()

    commit_data = response.json()

    # Extract file changes with diffs
    files = commit_data.get("files", [])
    commit_diff = {
        "commit_id": commit_sha,
        "message": commit_data.get("commit", {}).get("message", ""),
        "author": commit_data.get("commit", {}).get("author", {}),
        "files": [],
    }

    for file in files:
        file_info = {
            "filename": file.get("filename", ""),  # full path
            "status": file.get("status", ""),  # added, modified, removed
            "additions": file.get("additions", 0),
            "deletions": file.get("deletions", 0),
            "changes": file.get("changes", 0),
            "patch": file.get("patch", ""),  # The actual diff content
        }
        commit_diff["files"].append(file_info)

    return commit_diff
