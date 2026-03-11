from services.github.types.github_types import BaseArgs
from utils.command.run_subprocess import run_subprocess
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(raise_on_error=True)
def create_remote_branch(sha: str, base_args: BaseArgs) -> None:
    """Creates a remote branch pointing to the given SHA using git push.

    Requires clone_dir to be a valid git repo (EFS clone or local clone).
    """
    clone_url = base_args["clone_url"]
    branch_name = base_args["new_branch"]
    clone_dir = base_args["clone_dir"]

    run_subprocess(
        args=["git", "push", clone_url, f"{sha}:refs/heads/{branch_name}"],
        cwd=clone_dir,
    )
