# Standard imports
import os

# Local imports
from config import (
    PRODUCT_NAME,
    UTF8,
    GITHUB_APP_USER_NAME,
    GITHUB_APP_USER_ID,
    GITHUB_NOREPLY_EMAIL_DOMAIN,
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
from utils.error.handle_exceptions import handle_exceptions
from utils.command.run_command import run_command


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

    run_command(command="git init -b main", cwd=repo_path)
    run_command(command=f'git config user.name "{GITHUB_APP_USER_NAME}"', cwd=repo_path)
    run_command(
        command=f'git config user.email "{GITHUB_APP_USER_ID}+{GITHUB_APP_USER_NAME}@{GITHUB_NOREPLY_EMAIL_DOMAIN}"',
        cwd=repo_path,
    )
    run_command(command="git add README.md", cwd=repo_path)
    run_command(command='git commit -m "Initial commit with README"', cwd=repo_path)

    # Add authentication token to remote URL
    auth_remote_url = remote_url.replace("https://", f"https://x-access-token:{token}@")

    # Try to add remote, if it fails then set-url instead
    try:
        print(f"Adding remote: {remote_url}")
        run_command(command=f"git remote add origin {auth_remote_url}", cwd=repo_path)
        print("Remote added successfully")
    except Exception:  # pylint: disable=broad-except
        print(f"Setting remote: {remote_url}")
        run_command(
            command=f"git remote set-url origin {auth_remote_url}", cwd=repo_path
        )
        print("Remote set successfully")

    run_command(command="git push -u origin main", cwd=repo_path)
