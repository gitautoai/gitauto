# Third party imports
import subprocess
import json
from typing import Any
from requests import get

# Local imports
from config import GITHUB_API_URL, TIMEOUT
from services.github.create_headers import create_headers
from utils.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=False, raise_on_error=False)
def is_repo_forked(owner: str, repo: str, token: str):
    """https://docs.github.com/en/rest/repos/repos?apiVersion=2022-11-28#get-a-repository"""
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}"
    headers = create_headers(token=token)
    response = get(url=url, headers=headers, timeout=TIMEOUT)
    response.raise_for_status()
    is_fork: bool = response.json()["fork"]
    return is_fork


DEFAULT_REPO_STATS = {
    "file_count": 0,
    "blank_lines": 0,
    "comment_lines": 0,
    "code_lines": 0,
}


@handle_exceptions(default_return_value=DEFAULT_REPO_STATS, raise_on_error=False)
def get_repository_stats(local_path: str) -> dict[str, Any]:
    cloc_result = subprocess.run(
        ["cloc", local_path, "--json"], check=True, capture_output=True, text=True
    )

    # Parse cloc output
    cloc_data = json.loads(cloc_result.stdout)

    # Extract statistics
    file_count = cloc_data.get("header", {}).get("n_files", 0)
    blank_lines = cloc_data.get("SUM", {}).get("blank", 0)
    comment_lines = cloc_data.get("SUM", {}).get("comment", 0)
    code_lines = cloc_data.get("SUM", {}).get("code", 0)

    return {
        "file_count": file_count,
        "blank_lines": blank_lines,
        "comment_lines": comment_lines,
        "code_lines": code_lines,
    }
