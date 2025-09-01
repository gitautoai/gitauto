import json
import logging

import requests

from services.github.utils.create_headers import create_headers
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=[], raise_on_error=False)
def get_circleci_workflow_ids_from_check_suite(
    owner: str, repo: str, check_suite_id: int, github_token: str
):
    url = f"https://api.github.com/repos/{owner}/{repo}/check-suites/{check_suite_id}/check-runs"
    headers = create_headers(github_token)

    response = requests.get(url, headers=headers, timeout=30)

    if response.status_code != 200:
        logging.error(
            "Failed to get check runs for check suite %s: %s",
            check_suite_id,
            response.text,
        )
        return []

    data = response.json()
    check_runs = data.get("check_runs", [])

    workflow_ids = []
    for check_run in check_runs:
        external_id = check_run.get("external_id")
        if not external_id:
            continue

        external_data = json.loads(external_id)
        workflow_id = external_data.get("workflow-id")
        if workflow_id and workflow_id not in workflow_ids:
            workflow_ids.append(workflow_id)

    return workflow_ids
