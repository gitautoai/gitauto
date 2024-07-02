"""This is scheduled to run by AWS Lambda"""

import asyncio
from config import SUPABASE_SERVICE_ROLE_KEY, SUPABASE_URL
from services.gitauto_handler import handle_gitauto
from services.github.github_manager import (
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
    owner_type = "Organization"
    repo = "gitauto"
    default_branch = "main"
    user_id = 4620828
    user = "hiroshinishio"
    installation_id = supabase_manager.get_installation_id(owner_id=owner_id)
    token: str = get_installation_access_token(installation_id=installation_id)
    issue: IssueInfo | None = get_oldest_unassigned_open_issue(
        owner=owner, repo=repo, token=token
    )

    # Resolve that issue.
    payload = (
        {
            "issue": {
                "number": issue["number"],
                "title": issue["title"],
                "body": issue["body"],
            },
            "installation": {
                "id": installation_id,
            },
            "repository": {
                "owner": {
                    "type": owner_type,
                    "id": owner_id,
                    "login": owner,
                },
                "name": repo,
                "default_branch": default_branch,
            },
            "sender": {
                "id": user_id,
                "login": user,
            },
        },
    )

    # Use asyncio.run() to run the async function.
    asyncio.run(main=handle_gitauto(payload=payload, trigger_type="label"))
    return {"statusCode": 200}
