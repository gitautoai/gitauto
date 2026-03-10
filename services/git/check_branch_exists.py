from utils.command.run_subprocess import run_subprocess
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=False, raise_on_error=False)
def check_branch_exists(clone_url: str, branch_name: str):
    if not branch_name or not branch_name.strip():
        return False

    result = run_subprocess(
        args=["git", "ls-remote", "--heads", clone_url, f"refs/heads/{branch_name}"],
        cwd="/tmp",  # git ls-remote needs no local repo; /tmp is just a valid cwd
    )
    return bool(result.stdout.strip())
