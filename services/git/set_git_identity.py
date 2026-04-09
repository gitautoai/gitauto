from config import GITHUB_APP_GIT_EMAIL, GITHUB_APP_USER_NAME
from utils.command.run_subprocess import run_subprocess
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def set_git_identity(cwd: str):
    # Set GitAuto's git identity for commit attribution
    run_subprocess(["git", "config", "user.name", GITHUB_APP_USER_NAME], cwd)
    run_subprocess(["git", "config", "user.email", GITHUB_APP_GIT_EMAIL], cwd)
