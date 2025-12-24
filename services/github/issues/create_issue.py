import logging
from typing import cast
import requests
from config import GITHUB_API_URL, PRODUCT_ID, TIMEOUT
from services.github.types.issue import Issue
from services.github.utils.create_headers import create_headers
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=(500, None), raise_on_error=False)
def create_issue(
    *,
    owner: str,
    repo: str,
    token: str,
    title: str,
    body: str,
    assignees: list[str],
):
    """https://docs.github.com/en/rest/issues/issues?apiVersion=2022-11-28#create-an-issue"""
    labels = [PRODUCT_ID]

    payload = {
        "title": title,
        "body": body,
        "labels": labels,
    }

    if assignees:
        payload["assignees"] = assignees

    response = requests.post(
        url=f"{GITHUB_API_URL}/repos/{owner}/{repo}/issues",
        headers=create_headers(token=token),
        json=payload,
        timeout=TIMEOUT,
    )

    # If 422 error with invalid assignees, retry without assignees
    if (
        response.status_code == 422
        and assignees
        and "assignees" in response.text
        and "invalid" in response.text
    ):
        payload_without_assignees = {
            "title": title,
            "body": body,
            "labels": labels,
        }
        response = requests.post(
            url=f"{GITHUB_API_URL}/repos/{owner}/{repo}/issues",
            headers=create_headers(token=token),
            json=payload_without_assignees,
            timeout=TIMEOUT,
        )

    # Check for 410 Gone status - means issues are disabled for this repository
    if response.status_code == 410:
        logging.warning("Issues are disabled for repository %s/%s", owner, repo)
        return (410, None)

    response.raise_for_status()

    return (200, cast(Issue, response.json()))
