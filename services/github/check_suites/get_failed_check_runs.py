import requests

from config import GITHUB_API_URL, GITHUB_CHECK_RUN_FAILURES
from services.github.types.check_run import CheckRun
from services.github.utils.create_headers import create_headers
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=[], raise_on_error=False)
def get_failed_check_runs_from_check_suite(
    owner: str, repo: str, check_suite_id: int, github_token: str
):
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/check-suites/{check_suite_id}/check-runs"
    headers = create_headers(github_token)

    response = requests.get(url, headers=headers, timeout=30)

    if response.status_code != 200:
        print(
            f"Failed to get check runs for check suite {check_suite_id}: {response.text}"
        )
        empty_result: list[CheckRun] = []
        return empty_result

    data = response.json()
    check_runs: list[CheckRun] = data.get("check_runs", [])

    failed_check_runs = [
        cr for cr in check_runs if cr.get("conclusion") in GITHUB_CHECK_RUN_FAILURES
    ]

    return failed_check_runs
