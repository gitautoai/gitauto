import os
import shutil

from services.efs.get_efs_dir import get_efs_dir
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=False, raise_on_error=False)
def cleanup_repo_efs(owner: str, repo: str):
    repo_path = get_efs_dir(owner, repo)

    if not os.path.exists(repo_path):
        print(f"No EFS directory found for {owner}/{repo}, nothing to clean up")
        return False

    print(f"Deleting EFS directory: {repo_path}")
    shutil.rmtree(repo_path)
    print(f"Deleted EFS directory: {repo_path}")

    owner_path = os.path.dirname(repo_path)
    if os.path.exists(owner_path) and not os.listdir(owner_path):
        print(f"Owner directory {owner_path} is empty, removing it")
        os.rmdir(owner_path)
        print(f"Successfully removed owner directory {owner_path}")

    return True
