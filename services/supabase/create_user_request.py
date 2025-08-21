from services.supabase.issues.get_issue import get_issue
from services.supabase.issues.insert_issue import insert_issue
from services.supabase.usage.insert_usage import insert_usage, Trigger
from services.supabase.users.upsert_user import upsert_user
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=True)
def create_user_request(
    user_id: int,
    user_name: str,
    installation_id: int,
    owner_id: int,
    owner_type: str,
    owner_name: str,
    repo_id: int,
    repo_name: str,
    issue_number: int,
    source: str,
    trigger: Trigger,
    email: str | None,
    pr_number: int | None = None,
):
    existing_issue = get_issue(
        owner_type=owner_type,
        owner_name=owner_name,
        repo_name=repo_name,
        issue_number=issue_number,
    )

    if not existing_issue:
        insert_issue(
            owner_id=owner_id,
            owner_type=owner_type,
            owner_name=owner_name,
            repo_id=repo_id,
            repo_name=repo_name,
            issue_number=issue_number,
            installation_id=installation_id,
        )

    usage_id = insert_usage(
        owner_id=owner_id,
        owner_type=owner_type,
        owner_name=owner_name,
        repo_id=repo_id,
        repo_name=repo_name,
        issue_number=issue_number,
        user_id=user_id,
        installation_id=installation_id,
        source=source,
        trigger=trigger,
        pr_number=pr_number,
    )

    upsert_user(user_id=user_id, user_name=user_name, email=email)
    return usage_id
