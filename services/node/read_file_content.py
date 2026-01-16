import os

from config import UTF8
from services.github.files.get_raw_content import get_raw_content
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=None, raise_on_error=False)
def read_file_content(
    file_name: str,
    *,
    clone_dir: str | None,
    owner: str,
    repo: str,
    branch: str,
    token: str,
):
    if clone_dir:
        local_path = os.path.join(clone_dir, file_name)
        if os.path.exists(local_path):
            with open(local_path, "r", encoding=UTF8) as f:
                content = f.read()
            logger.info("node: Read %s from %s", file_name, local_path)
            return content

    content = get_raw_content(
        owner=owner, repo=repo, file_path=file_name, ref=branch, token=token
    )
    if content:
        logger.info("node: Fetched %s from GitHub API", file_name)
    return content
