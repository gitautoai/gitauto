# Standard imports
import logging

# Third-party imports
import requests

# Local imports
from config import (
    GITHUB_API_URL,
    TIMEOUT,
)

# Local imports (GitHub)
from services.github.comments.update_comment import update_comment
from services.github.repositories.initialize_repo import initialize_repo
from services.github.utils.create_headers import create_headers
from services.github.types.github_types import BaseArgs

# Local imports (Utils)
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(raise_on_error=True)
def get_latest_remote_commit_sha(clone_url: str, base_args: BaseArgs) -> str:
    """SHA stands for Secure Hash Algorithm. It's a unique identifier for a commit.
    https://docs.github.com/en/rest/git/refs?apiVersion=2022-11-28#get-a-reference"""
    owner, repo, branch = (
        base_args["owner"],
        base_args["repo"],
        base_args["base_branch"],
    )
    token = base_args["token"]
    try:
        response: requests.Response = requests.get(
            url=f"{GITHUB_API_URL}/repos/{owner}/{repo}/git/ref/heads/{branch}",
            headers=create_headers(token=token),
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        return response.json()["object"]["sha"]
    except requests.exceptions.HTTPError as e:
        if (
            e.response.status_code == 409
            and e.response.json()["message"] == "Git Repository is empty."
        ):
            msg = "Repository is empty. So, creating an initial empty commit."
            logging.info(msg)
            repo_path = f"/tmp/repo/{owner}-{repo}"
            initialize_repo(repo_path=repo_path, remote_url=clone_url, token=token)
            return get_latest_remote_commit_sha(
                clone_url=clone_url, base_args=base_args
            )
        raise
    except Exception as e:
        msg = f"{get_latest_remote_commit_sha.__name__} encountered an error: {e}"
        update_comment(body=msg, base_args=base_args)
        # Raise an error because we can't continue without the latest commit SHA
        raise RuntimeError(
            f"Error: Could not get the latest commit SHA in {get_latest_remote_commit_sha.__name__}"
        ) from e
