# Standard imports
import re

# Local imports
from utils.command.run_subprocess import run_subprocess
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=0, raise_on_error=False)
def count_repo_total_lines(local_path: str):
    # Get empty tree SHA to diff against (counts all lines in HEAD as insertions)
    empty_tree = run_subprocess(
        args=["git", "hash-object", "-t", "tree", "/dev/null"],
        cwd=local_path,
    )
    empty_tree_sha = empty_tree.stdout.strip()

    diff_result = run_subprocess(
        args=["git", "diff", "--shortstat", empty_tree_sha, "HEAD"],
        cwd=local_path,
    )
    diff_output = (
        diff_result.stdout.strip() if diff_result and diff_result.stdout else ""
    )

    match = re.search(r"(\d+) insertions?\(\+\)", diff_output)
    if not match:
        logger.info("No lines found in %s", local_path)
        return 0

    line_count = int(match.group(1))
    logger.info("Counted %d lines in %s", line_count, local_path)
    return line_count
