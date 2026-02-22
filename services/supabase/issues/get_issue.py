# Standard imports
from typing import cast

# Third-party imports
from schemas.supabase.types import Issues

# Local imports
from services.supabase.client import supabase
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def get_issue(
    owner_type: str,
    owner_name: str,
    repo_name: str,
    pr_number: int,
):
    result = (
        supabase.table(table_name="issues")
        .select("*")
        .eq(column="owner_type", value=owner_type)
        .eq(column="owner_name", value=owner_name)
        .eq(column="repo_name", value=repo_name)
        .eq(column="issue_number", value=pr_number)
        .execute()
    )
    if not result.data:
        return None
    return cast(Issues, result.data[0])
