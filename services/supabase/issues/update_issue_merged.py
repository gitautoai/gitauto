from services.supabase.client import supabase
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def update_issue_merged(
    owner_type: str,
    owner_name: str,
    repo_name: str,
    issue_number: int,
    merged: bool = True,
):
    (
        supabase.table(table_name="issues")
        .update(json={"merged": merged})
        .eq(column="owner_type", value=owner_type)
        .eq(column="owner_name", value=owner_name)
        .eq(column="repo_name", value=repo_name)
        .eq(column="issue_number", value=issue_number)
        .execute()
    )
