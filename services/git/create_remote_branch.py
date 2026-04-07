from services.types.base_args import BaseArgs
from utils.command.run_subprocess import run_subprocess
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(raise_on_error=True)
def create_remote_branch(sha: str, base_args: BaseArgs) -> None:
    """Creates a remote branch pointing to the given SHA using git push.

    Requires clone_dir to be a valid git repo.
    """
    clone_url = base_args["clone_url"]
    base_branch = base_args["base_branch"]
    branch_name = base_args["new_branch"]
    clone_dir = base_args["clone_dir"]

    # Repos are shallow (--depth 1) so the SHA from ls-remote may not exist locally.
    # Fetch the base branch first to ensure the latest commit object is available.
    run_subprocess(
        args=["git", "fetch", clone_url, base_branch],
        cwd=clone_dir,
    )

    run_subprocess(
        args=["git", "push", clone_url, f"{sha}:refs/heads/{branch_name}"],
        cwd=clone_dir,
    )
