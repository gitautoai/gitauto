# Standard imports
import os

# Local imports
from config import (
    GITHUB_APP_GIT_EMAIL,
    GITHUB_APP_USER_NAME,
    PRODUCT_NAME,
    UTF8,
)
from constants.urls import (
    BLOG_URL,
    PRODUCT_DEMO_URL,
    PRODUCT_LINKEDIN_URL,
    PRODUCT_TWITTER_URL,
    PRODUCT_URL,
    PRODUCT_YOUTUBE_URL,
)

# Local imports (Utils)
from utils.command.run_subprocess import run_subprocess
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=None, raise_on_error=False)
def initialize_repo(repo_path: str, remote_url: str, token: str) -> None:
    """Initialize a repository with a README.md file and push it to the remote. It didn't work without a README.md file."""
    if not os.path.exists(path=repo_path):
        os.makedirs(name=repo_path)

    # Create README.md
    readme_content = f"""## {PRODUCT_NAME} resources\n\nHere are GitAuto resources.\n\n- [GitAuto homepage]({PRODUCT_URL})\n- [GitAuto demo]({PRODUCT_DEMO_URL})\n- [GitAuto use cases]({BLOG_URL})\n- [GitAuto LinkedIn]({PRODUCT_LINKEDIN_URL})\n- [GitAuto Twitter]({PRODUCT_TWITTER_URL})\n- [GitAuto YouTube]({PRODUCT_YOUTUBE_URL})\n"""
    readme_path = os.path.join(repo_path, "README.md")
    with open(readme_path, "w", encoding=UTF8) as f:
        f.write(readme_content)

    run_subprocess(["git", "init", "-b", "main"], repo_path)
    run_subprocess(["git", "config", "user.name", GITHUB_APP_USER_NAME], repo_path)
    run_subprocess(["git", "config", "user.email", GITHUB_APP_GIT_EMAIL], repo_path)
    run_subprocess(["git", "add", "README.md"], repo_path)
    run_subprocess(["git", "commit", "-m", "Initial commit with README"], repo_path)

    # Add authentication token to remote URL
    auth_remote_url = remote_url.replace("https://", f"https://x-access-token:{token}@")

    # Try to add remote, if it fails then set-url instead
    try:
        logger.info("Adding remote: %s", remote_url)
        run_subprocess(["git", "remote", "add", "origin", auth_remote_url], repo_path)
        logger.info("Remote added successfully")
    except Exception:  # pylint: disable=broad-except
        logger.info("Setting remote: %s", remote_url)
        run_subprocess(
            ["git", "remote", "set-url", "origin", auth_remote_url], repo_path
        )
        logger.info("Remote set successfully")

    run_subprocess(["git", "push", "-u", "origin", "main"], repo_path)
