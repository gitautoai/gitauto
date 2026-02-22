from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(raise_on_error=True)
def get_impl_file_from_pr_title(pr_title: str):
    if not pr_title:
        raise ValueError("pr_title is empty")

    last_token = pr_title.split()[-1]
    if "/" in last_token or "." in last_token:
        return last_token

    raise ValueError(f"No file path found in PR title: {pr_title}")
