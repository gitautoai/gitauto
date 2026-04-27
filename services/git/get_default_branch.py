# Local imports
from utils.command.run_subprocess import run_subprocess
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=None, raise_on_error=True)
def get_default_branch(clone_url: str):
    """Returns the default branch name, or None if the repo is empty or disabled.

    Uses `git ls-remote --symref URL HEAD` which does NOT require a local clone.
    """
    try:
        result = run_subprocess(
            args=["git", "ls-remote", "--symref", clone_url, "HEAD"],
            cwd="/tmp",
        )
    except ValueError as err:
        # Customer disabled the repo (e.g. owner ran out of quota, ToS violation, manual disable). Sentry AGENT-30B and the cascade AGENT-3KQ/AGENT-3J5 (qenex-ai/metamask-extension): GitHub returns 403 with "Repository ... is disabled. Please ask the owner to check their account." Match the marker, log info, return None — callers already treat None as "empty repo, skip".
        if "is disabled" in str(err):
            logger.info("get_default_branch: repository disabled by owner, skipping")
            return None
        raise
    output = result.stdout.strip() if result and result.stdout else ""

    if not output:
        logger.info("Repository appears empty (no refs)")
        return None

    # Parse "ref: refs/heads/main\tHEAD" from the symref line
    prefix = "ref: refs/heads/"
    suffix = "\tHEAD"
    for line in output.split("\n"):
        if line.startswith(prefix) and line.endswith(suffix):
            branch = line[len(prefix) : -len(suffix)]
            logger.info("get_default_branch: parsed default branch %s", branch)
            return branch

    # Fallback: if symref line not found but SHA line exists, repo is not empty but we can't determine default branch name — use "main" as fallback.
    logger.warning("Could not parse default branch from ls-remote output: %s", output)
    return "main"
