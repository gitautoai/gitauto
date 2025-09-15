from typing import Literal, cast
from services.supabase.client import supabase
from utils.error.handle_exceptions import handle_exceptions


Trigger = Literal[
    "issue_label",
    "issue_comment",
    "review_comment",
    "test_failure",
    "pr_checkbox",
    "pr_merge",
    # "push",
    # "schedule",
]


@handle_exceptions(default_return_value=None, raise_on_error=False)
def insert_usage(
    owner_id: int,
    owner_type: str,
    owner_name: str,
    repo_id: int,
    repo_name: str,
    issue_number: int,
    user_id: int,
    installation_id: int,
    source: str,
    trigger: Trigger,
    pr_number: int | None = None,
    lambda_log_group: str | None = None,
    lambda_log_stream: str | None = None,
    lambda_request_id: str | None = None,
):
    data, _ = (
        supabase.table(table_name="usage")
        .insert(
            json={
                "owner_id": owner_id,
                "owner_type": owner_type,
                "owner_name": owner_name,
                "repo_id": repo_id,
                "repo_name": repo_name,
                "issue_number": issue_number,
                "user_id": user_id,
                "installation_id": installation_id,
                "source": source,
                "trigger": trigger,
                "pr_number": pr_number,
                "lambda_log_group": lambda_log_group,
                "lambda_log_stream": lambda_log_stream,
                "lambda_request_id": lambda_request_id,
            }
        )
        .execute()
    )
    return cast(int, data[1][0]["id"])
