from services.supabase.client import supabase
from services.website.get_default_structured_rules import get_default_structured_rules
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def insert_repository(
    owner_id: int,
    repo_id: int,
    repo_name: str,
    user_id: int,
    user_name: str,
    file_count: int = 0,
    blank_lines: int = 0,
    comment_lines: int = 0,
    code_lines: int = 0,
):
    structured_rules = get_default_structured_rules()

    insert_result = (
        supabase.table("repositories")
        .insert(
            {
                "owner_id": owner_id,
                "repo_id": repo_id,
                "repo_name": repo_name,
                "file_count": file_count,
                "blank_lines": blank_lines,
                "comment_lines": comment_lines,
                "code_lines": code_lines,
                "structured_rules": structured_rules,
                "created_by": str(user_id) + ":" + user_name,
                "updated_by": str(user_id) + ":" + user_name,
            }
        )
        .execute()
    )

    return insert_result.data[0] if insert_result.data else None
