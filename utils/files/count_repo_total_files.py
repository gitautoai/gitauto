# Local imports
from utils.command.run_subprocess import run_subprocess
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=0, raise_on_error=False)
def count_repo_total_files(local_path: str):
    result = run_subprocess(
        args=["git", "ls-tree", "-r", "--name-only", "HEAD"],
        cwd=local_path,
    )
    output = result.stdout.strip() if result and result.stdout else ""
    if not output:
        logger.info("No files found in %s", local_path)
        return 0

    file_count = len(output.split("\n"))
    logger.info("Counted %d files in %s", file_count, local_path)
    return file_count
