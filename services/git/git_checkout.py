from utils.command.run_subprocess import run_subprocess
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=False, raise_on_error=False)
def git_checkout(target_dir: str, branch: str):
    logger.info("Checking out branch %s in %s", branch, target_dir)

    # Syntax: git checkout [options] <branch> [<start-point>]
    # -f discards local changes, -B creates/resets branch to FETCH_HEAD (set by prior git fetch)
    run_subprocess(["git", "checkout", "-f", "-B", branch, "FETCH_HEAD"], target_dir)

    logger.info("git checkout completed: %s", target_dir)
    return True
