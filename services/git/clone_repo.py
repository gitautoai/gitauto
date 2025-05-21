import subprocess
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(raise_on_error=True)
def clone_repo(owner: str, repo: str, token: str, target_dir: str):
    repo_url = f"https://x-access-token:{token}@github.com/{owner}/{repo}.git"
    clone_cmd = f"git clone {repo_url} {target_dir}"
    subprocess.run(clone_cmd, shell=True, capture_output=True, text=True, check=True)
