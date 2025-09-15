from services.supabase.client import supabase
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def update_usage(
    usage_id: int,
    token_input: int,
    token_output: int,
    total_seconds: int,
    is_completed: bool = True,
    pr_number: int | None = None,
    retry_workflow_id_hash_pairs: list[str] | None = None,
    original_error_log: str | None = None,
    minimized_error_log: str | None = None,
    lambda_log_group: str | None = None,
    lambda_log_stream: str | None = None,
    lambda_request_id: str | None = None,
):
    """Add agent information to usage record and set is_completed to True."""
    update_data = {
        "is_completed": is_completed,
        "pr_number": pr_number,
        "token_input": token_input,
        "token_output": token_output,
        "total_seconds": total_seconds,
    }

    if retry_workflow_id_hash_pairs is not None:
        update_data["retry_workflow_id_hash_pairs"] = retry_workflow_id_hash_pairs

    if original_error_log is not None:
        update_data["original_error_log"] = original_error_log

    if minimized_error_log is not None:
        update_data["minimized_error_log"] = minimized_error_log

    if lambda_log_group is not None:
        update_data["lambda_log_group"] = lambda_log_group

    if lambda_log_stream is not None:
        update_data["lambda_log_stream"] = lambda_log_stream

    if lambda_request_id is not None:
        update_data["lambda_request_id"] = lambda_request_id

    supabase.table(table_name="usage").update(json=update_data).eq(
        column="id", value=usage_id
    ).execute()
