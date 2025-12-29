import logging

from utils.handle_exceptions import handle_exceptions

import requests
from config import GITHUB_API_URL, GITHUB_CHECK_RUN_FAILURES
from services.github.token.create_headers import create_headers
from services.github.types.check_run import CheckRun


@handle_exceptions(default_return_value=[])
def get_failed_check_runs_from_check_suite(
    owner: str, repo: str, check_suite_id: int, github_token: str
) -> list[CheckRun]:
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/check-suites/{check_suite_id}/check-runs"
    headers = create_headers(github_token)
    response = requests.get(url, headers=headers, timeout=30)

    if response.status_code != 200:
        logging.error(
            "Failed to get check runs for check suite %s: %s",
            check_suite_id,
            response.text,
        )
        empty_result: list[CheckRun] = []
        return empty_result

    data = response.json()
    check_runs = data.get("check_runs", [])

    failed_check_runs = [
        run for run in check_runs if run.get("conclusion") in GITHUB_CHECK_RUN_FAILURES
    ]

    return failed_check_runs
