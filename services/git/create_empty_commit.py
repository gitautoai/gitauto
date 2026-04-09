from services.types.base_args import BaseArgs
from utils.command.run_subprocess import run_subprocess
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=False, raise_on_error=False)
def create_empty_commit(
    base_args: BaseArgs,
    message: str = "Empty commit to trigger final tests",
):
    clone_url = base_args["clone_url"]
    branch = base_args["new_branch"]
    clone_dir = base_args["clone_dir"]

    # --no-verify skips pre-commit hooks (e.g. lint-staged) that fail in Lambda sandbox because npm can't mkdir /home/sbx_user1051
    run_subprocess(
        args=["git", "commit", "--allow-empty", "--no-verify", "-m", message],
        cwd=clone_dir,
    )
    run_subprocess(
        args=["git", "push", clone_url, f"HEAD:refs/heads/{branch}"],
        cwd=clone_dir,
    )
    return True
