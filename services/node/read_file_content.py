import os

from config import UTF8
from services.github.files.get_raw_content import get_raw_content
from utils.error.handle_exceptions import handle_exceptions
from utils.files.read_local_file import read_local_file
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=None, raise_on_error=False)
def read_file_content(
    file_name: str,
    *,
    local_dir: str,
    owner: str,
    repo: str,
    branch: str,
    token: str,
):
    content = read_local_file(file_name, base_dir=local_dir)
    if content:
        return content

    # Fallback: fetch from GitHub API
    content = get_raw_content(
        owner=owner, repo=repo, file_path=file_name, ref=branch, token=token
    )
    if content:
        logger.info("Fetched %s from GitHub API", file_name)

        # Save to local_dir so subsequent calls find it locally
        local_path = os.path.join(local_dir, file_name)
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        with open(local_path, "w", encoding=UTF8) as f:
            f.write(content)

    return content
