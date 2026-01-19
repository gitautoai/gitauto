from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value="", raise_on_error=False)
def get_clone_url(owner: str, repo: str, token: str):
    return f"https://x-access-token:{token}@github.com/{owner}/{repo}.git"
