import requests

from config import TIMEOUT
from services.git.tree import Tree
from utils.logging.logging_config import logger


def get_github_file_tree(owner: str, repo: str, ref: str, token: str):
    """Fallback for get_file_tree via GitHub Trees API. When a user installs GitAuto and immediately visits the file coverage page, the local EFS clone hasn't completed yet, so we fetch the tree from GitHub API instead. We want to be platform-agnostic and remove GitHub API calls as much as possible, but can't remove this one."""
    tree_items: list[Tree] = []

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }
    url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{ref}?recursive=1"
    response = requests.get(url, headers=headers, timeout=TIMEOUT)

    if response.status_code != 200:
        logger.warning(
            "GitHub Trees API failed for %s/%s ref=%s: %s",
            owner,
            repo,
            ref,
            response.status_code,
        )
        return tree_items

    data = response.json()
    if data.get("truncated"):
        logger.warning("GitHub tree truncated for %s/%s (too many files)", owner, repo)
    for item in data.get("tree", []):
        tree_entry: Tree = {
            "path": item["path"],
            "mode": item["mode"],
            "type": item["type"],
            "sha": item["sha"],
        }
        if "size" in item:
            tree_entry["size"] = item["size"]
        tree_items.append(tree_entry)

    return tree_items
