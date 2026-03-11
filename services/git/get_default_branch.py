# Local imports
from utils.command.run_subprocess import run_subprocess
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=None, raise_on_error=True)
def get_default_branch(clone_url: str):
    """Returns the default branch name, or None if the repo is empty.

    Uses `git ls-remote --symref URL HEAD` which does NOT require a local clone.
    """
    result = run_subprocess(
        args=["git", "ls-remote", "--symref", clone_url, "HEAD"],
        cwd="/tmp",
    )
    output = result.stdout.strip() if result and result.stdout else ""

    if not output:
        logger.info("Repository appears empty (no refs)")
        return None

    # Parse "ref: refs/heads/main\tHEAD" from the symref line
    prefix = "ref: refs/heads/"
    suffix = "\tHEAD"
    for line in output.split("\n"):
        if line.startswith(prefix) and line.endswith(suffix):
            return line[len(prefix) : -len(suffix)]

    # Fallback: if symref line not found but SHA line exists, repo is not empty
    # but we can't determine default branch name - use "main" as fallback
    logger.warning("Could not parse default branch from ls-remote output: %s", output)
    return "main"
