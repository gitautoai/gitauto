from services.github.comments.update_comment import update_comment
from services.git.initialize_repo import initialize_repo
from services.github.types.github_types import BaseArgs
from utils.command.run_subprocess import run_subprocess
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(raise_on_error=True)
def get_latest_remote_commit_sha(clone_url: str, base_args: BaseArgs) -> str:
    owner = base_args["owner"]
    repo = base_args["repo"]
    branch = base_args["base_branch"]
    token = base_args["token"]
    try:
        result = run_subprocess(
            args=["git", "ls-remote", clone_url, f"refs/heads/{branch}"],
            cwd="/tmp",  # git ls-remote needs no local repo; /tmp is just a valid cwd
        )
        output = result.stdout.strip()
        if not output:
            msg = "Repository is empty. So, creating an initial empty commit."
            logger.info(msg)
            repo_path = f"/tmp/repo/{owner}-{repo}"
            initialize_repo(repo_path=repo_path, remote_url=clone_url, token=token)
            return get_latest_remote_commit_sha(
                clone_url=clone_url, base_args=base_args
            )
        return output.split("\t")[0]

    except Exception as e:
        msg = f"{get_latest_remote_commit_sha.__name__} encountered an error: {e}"
        update_comment(body=msg, base_args=base_args)

        # Raise an error because we can't continue without the latest commit SHA
        raise RuntimeError(
            f"Error: Could not get the latest commit SHA in {get_latest_remote_commit_sha.__name__}"
        ) from e
