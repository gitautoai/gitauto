from utils.command.run_subprocess import run_subprocess
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def get_reference(clone_url: str, branch: str):
    result = run_subprocess(
        args=["git", "ls-remote", clone_url, f"refs/heads/{branch}"],
        cwd="/tmp",  # git ls-remote needs no local repo; /tmp is just a valid cwd
    )
    output = result.stdout.strip()
    if not output:
        return None

    return output.split("\t")[0]
