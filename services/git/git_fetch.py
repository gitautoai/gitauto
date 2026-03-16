import os

from services.git.resolve_git_locks import resolve_git_locks
from utils.command.run_subprocess import run_subprocess
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=False, raise_on_error=False)
def git_fetch(target_dir: str, clone_url: str, branch: str):
    # Remove stale locks (>10min, crashed Lambda) and wait for fresh ones (concurrent Lambda)
    efs_git_dir = os.path.join(target_dir, ".git")
    resolve_git_locks(efs_git_dir)

    # --depth 1 for shallow fetch to save disk space and time
    # Syntax: git fetch [options] <repository> <refspec>
    run_subprocess(["git", "fetch", "--depth", "1", clone_url, branch], target_dir)

    logger.info("git fetch completed: %s", target_dir)
    return True
