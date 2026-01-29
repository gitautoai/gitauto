from datetime import datetime
from services.supabase.client import supabase
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=set(), raise_on_error=False)
def count_unique_requests(installation_id: int, start_date: datetime):
    result = (
        supabase.table("usage")
        .select("owner_type, owner_name, repo_name, pr_number")
        .gt("created_at", start_date)
        .eq("installation_id", installation_id)
        .in_(
            "trigger",
            [
                "issue_comment",
                "issue_label",
                "pull_request",
            ],
        )
        # .eq("is_completed", True)
        .execute()
    )

    # Process unique requests in Python by combining fields
    unique_requests = {
        f"{record['owner_type']}/{record['owner_name']}/{record['repo_name']}#{record['pr_number']}"
        for record in result.data
    }

    return unique_requests
