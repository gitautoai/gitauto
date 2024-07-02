"""This is scheduled to run by AWS Lambda"""

from config import PRODUCT_ID, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_URL
from services.github.github_manager import (
    add_label_to_issue,
    get_installation_access_token,
    get_oldest_unassigned_open_issue,
)
from services.github.github_types import IssueInfo
from services.supabase import SupabaseManager

supabase_manager = SupabaseManager(url=SUPABASE_URL, key=SUPABASE_SERVICE_ROLE_KEY)


def schedule_handler(event, context) -> dict[str, int]:
    print(f"Event: {event}")
    print(f"Context: {context}")

    # List installed and paid repositories.

    # Check available remaining counts for each repository and exclude those with zero or less.

    # Identify the oldest open and unassigned issue for each repository.
    owner_id = 159883862  # gitautoai
    owner = "gitautoai"
    repo = "gitauto"
    installation_id = supabase_manager.get_installation_id(owner_id=owner_id)
    token: str = get_installation_access_token(installation_id=installation_id)
    issue: IssueInfo | None = get_oldest_unassigned_open_issue(
        owner=owner, repo=repo, token=token
    )
    issue_number = issue["number"]

    # Label the issue with the product ID to trigger GitAuto.
    add_label_to_issue(
        owner=owner, repo=repo, issue_number=issue_number, label=PRODUCT_ID, token=token
    )
    return {"statusCode": 200}
