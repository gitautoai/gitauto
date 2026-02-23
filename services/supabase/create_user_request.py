from constants.triggers import Trigger
from services.supabase.usage.insert_usage import insert_usage
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
    pr_number: int,
    source: str,
    trigger: Trigger,
    email: str | None,
    lambda_info: dict[str, str | None] | None = None,
):
    # Extract Lambda context info if provided
    lambda_log_group = lambda_info.get("log_group") if lambda_info else None
    lambda_log_stream = lambda_info.get("log_stream") if lambda_info else None
    lambda_request_id = lambda_info.get("request_id") if lambda_info else None

    usage_id = insert_usage(
        owner_id=owner_id,
        owner_type=owner_type,
        owner_name=owner_name,
        repo_id=repo_id,
        repo_name=repo_name,
        pr_number=pr_number,
        user_id=user_id,
        user_name=user_name,
        installation_id=installation_id,
        source=source,
        trigger=trigger,
        lambda_log_group=lambda_log_group,
        lambda_log_stream=lambda_log_stream,
        lambda_request_id=lambda_request_id,
    )

    upsert_user(user_id=user_id, user_name=user_name, email=email)
    return usage_id
