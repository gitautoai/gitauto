import os
import shutil
import tempfile

from config import GITHUB_APP_GIT_EMAIL, GITHUB_APP_USER_NAME
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

    # If clone_dir exists and is a git repo, use it directly
    if clone_dir and os.path.isdir(os.path.join(clone_dir, ".git")):
        cwd = clone_dir
        tmp_dir = None
    else:
        # Temp shallow clone for callers without a local clone
        tmp_dir = tempfile.mkdtemp(prefix="gitauto-empty-commit-")
        run_subprocess(
            args=[
                "git",
                "clone",
                "--depth",
                "1",
                "--branch",
                branch,
                clone_url,
                tmp_dir,
            ],
            cwd="/tmp",
        )
        cwd = tmp_dir

    try:
        run_subprocess(["git", "config", "user.name", GITHUB_APP_USER_NAME], cwd)
        run_subprocess(["git", "config", "user.email", GITHUB_APP_GIT_EMAIL], cwd)

        # --no-verify skips pre-commit hooks (e.g. lint-staged) that fail in Lambda sandbox because npm can't mkdir /home/sbx_user1051
        run_subprocess(
            args=["git", "commit", "--allow-empty", "--no-verify", "-m", message],
            cwd=cwd,
        )
        run_subprocess(
            args=["git", "push", clone_url, f"HEAD:refs/heads/{branch}"],
            cwd=cwd,
        )
        return True
    finally:
        if tmp_dir:
            shutil.rmtree(tmp_dir, ignore_errors=True)
