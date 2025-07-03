import logging
import requests
from config import GITHUB_API_URL, TIMEOUT
from services.github.types.tree import Tree
from services.github.utils.create_headers import create_headers
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=[], raise_on_error=False)
def get_file_tree(owner: str, repo: str, ref: str, token: str):
    """https://docs.github.com/en/rest/git/trees?apiVersion=2022-11-28#get-a-tree"""
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/git/trees/{ref}"
    headers = create_headers(token=token)
    params = {"recursive": 1}
    response = requests.get(url=url, headers=headers, params=params, timeout=TIMEOUT)

    tree_items: list[Tree] = []
    if response.status_code == 409 and "Git Repository is empty" in response.text:
        return tree_items

    if response.status_code == 404:
        return tree_items

    response.raise_for_status()

    if response.json().get("truncated"):
        msg = f"Repository tree for `{owner}/{repo}` was truncated by GitHub API. Use the non-recursive method of fetching trees, and fetch one sub-tree at a time. See https://docs.github.com/en/rest/git/trees?apiVersion=2022-11-28#get-a-tree"
        logging.warning(msg)

    tree_items = response.json().get("tree", [])
    return tree_items
