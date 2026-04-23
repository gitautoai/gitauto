from utils.command.run_subprocess import run_subprocess
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value="", raise_on_error=False)
def get_local_head_sha(clone_dir: str):
    result = run_subprocess(args=["git", "rev-parse", "HEAD"], cwd=clone_dir)
    sha = result.stdout.strip()
    logger.info("Local HEAD in %s: %s", clone_dir, sha)
    return sha
