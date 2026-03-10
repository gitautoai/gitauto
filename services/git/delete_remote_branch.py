from services.github.types.github_types import BaseArgs
from utils.command.run_subprocess import run_subprocess
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=False, raise_on_error=False)
def delete_remote_branch(base_args: BaseArgs):
    clone_url = base_args["clone_url"]
    branch_name = base_args["new_branch"]
    clone_dir = base_args["clone_dir"]

    run_subprocess(
        args=["git", "push", clone_url, "--delete", branch_name],
        cwd=clone_dir,
    )
    return True
