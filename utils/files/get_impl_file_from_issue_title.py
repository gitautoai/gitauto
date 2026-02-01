from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(raise_on_error=True)
def get_impl_file_from_issue_title(issue_title: str):
    if not issue_title:
        raise ValueError("issue_title is empty")

    last_token = issue_title.split()[-1]
    if "/" in last_token or "." in last_token:
        return last_token

    raise ValueError(f"No file path found in issue title: {issue_title}")
