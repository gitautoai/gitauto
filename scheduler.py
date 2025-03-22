"""This is scheduled to run by AWS Lambda"""

import logging
import time
from config import PRODUCT_ID
from services.github.github_manager import (
    add_label_to_issue,
    get_installation_access_token,
    get_installed_owners_and_repos,
    get_oldest_unassigned_open_issue,
)
from services.github.github_types import IssueInfo
from services.supabase.gitauto_manager import get_installation_ids
from services.supabase.users_manager import get_how_many_requests_left_and_cycle


def schedule_handler(_event, _context) -> dict[str, int]:
    return
    print("\n" * 3 + "-" * 70)

    # Get all active installation IDs from Supabase including free customers.
    installation_ids: list[int] = get_installation_ids()

    # Get all owners and repositories from GitHub.
    for installation_id in installation_ids:
        # Pause for 1+ second to avoid secondary rate limits. https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api?apiVersion=2022-11-28#pause-between-mutative-requests
        time.sleep(1)

        # Get the installation access token for each installation ID.
        token = get_installation_access_token(installation_id=installation_id)
        if token is None:
            msg = f"Token is None for installation_id: {installation_id}, so skipping"
            logging.info(msg)
            continue

        # Get all owners and repositories for each installation ID.
        owners_repos = get_installed_owners_and_repos(token=token)

        # Process each owner and repository.
        for owner_repo in owners_repos:
            owner_id: int = owner_repo["owner_id"]
            owner: str = owner_repo["owner"]
            repo: str = owner_repo["repo"]
            logging.info("Processing %s/%s", owner, repo)

            # Identify an oldest, open, unassigned, and not gitauto labeled issue for each repository.
            issue: IssueInfo | None = get_oldest_unassigned_open_issue(
                owner=owner, repo=repo, token=token
            )
            logging.info("Issue: %s", issue)

            # Continue to the next set of owners and repositories if there is no open issue.
            if issue is None:
                continue

            # Extract the issue number if there is an open issue.
            issue_number = issue["number"]

            # Check the remaining available usage count, continue if it's less than 1.
            requests_left, _request_count, _end_date, _is_retried = (
                get_how_many_requests_left_and_cycle(
                    installation_id=installation_id,
                    owner_id=owner_id,
                    owner_name=owner,
                    issue_id=issue_number,
                )
            )
            if requests_left < 1:
                msg = f"Requests left: {requests_left} for owner: {owner}, repo: {repo}, issue_number: {issue_number}, so skipping"
                logging.info(msg)
                continue

            # Label the issue with the product ID to trigger GitAuto.
            time.sleep(1)
            add_label_to_issue(
                owner=owner,
                repo=repo,
                issue_number=issue_number,
                label=PRODUCT_ID,
                token=token,
            )
