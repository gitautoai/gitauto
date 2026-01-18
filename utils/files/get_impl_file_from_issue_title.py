from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def get_impl_file_from_issue_title(issue_title: str):
    if not issue_title:
        return None
    last_token = issue_title.split()[-1]
    if "/" in last_token or "." in last_token:
        return last_token
    return None
