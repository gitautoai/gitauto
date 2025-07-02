from constants.messages import SETTINGS_LINKS
from constants.urls import GH_BASE_URL


def get_issue_title(file_path: str):
    return f"Schedule: Add unit tests to {file_path}"


def get_issue_body(
    owner: str,
    repo: str,
    branch: str,
    file_path: str,
    statement_coverage: float | None,
):
    file_url = f"{GH_BASE_URL}/{owner}/{repo}/blob/{branch}/{file_path}"

    if statement_coverage is None:
        return f"Add unit tests for [{file_path}]({file_url}).\n\n{SETTINGS_LINKS}"

    return (
        f"Add unit tests for [{file_path}]({file_url}) (Coverage: {statement_coverage}%).\n\n"
        f"{SETTINGS_LINKS}"
    )
