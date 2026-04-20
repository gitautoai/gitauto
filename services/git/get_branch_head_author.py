from utils.command.run_subprocess import run_subprocess
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value="unknown", raise_on_error=False)
def get_branch_head_author(clone_dir: str, clone_url: str, branch: str):
    """Fetch the remote branch tip and return its last commit's author string in the form "Name <email>". Used by callers that need to log who won a push race. Returns "unknown" if anything in the fetch/log pipeline fails — callers should not make control-flow decisions on the value."""
    run_subprocess(["git", "fetch", clone_url, branch], clone_dir)
    result = run_subprocess(
        ["git", "log", "FETCH_HEAD", "-1", "--format=%an <%ae>"], clone_dir
    )
    author = result.stdout.strip()
    logger.info("get_branch_head_author: %s on %s = %s", clone_dir, branch, author)
    return author
