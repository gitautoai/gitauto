# Local imports
from services.supabase.client import supabase
from services.supabase.owners.create_owner import create_owner
from services.supabase.owners.get_owner import get_owner
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def upsert_repository(
    owner_id: int,
    owner_name: str,
    repo_id: int,
    repo_name: str,
    user_id: int,
    user_name: str,
    file_count: int = 0,
    blank_lines: int = 0,
    comment_lines: int = 0,
    code_lines: int = 0,
):
    # First check if owner exists since it's a foreign key
    owner = get_owner(owner_id)

    # If owner doesn't exist, create it
    if not owner:
        create_owner(
            owner_id=owner_id,
            owner_name=owner_name,
            user_id=user_id,
            user_name=user_name,
        )

    # Check if repository already exists
    result = supabase.table("repositories").select("*").eq("repo_id", repo_id).execute()

    if result.data:
        # Update existing repository
        update_result = (
            supabase.table("repositories")
            .update(
                {
                    "updated_by": user_id + ":" + user_name,
                    "file_count": file_count,
                    "blank_lines": blank_lines,
                    "comment_lines": comment_lines,
                    "code_lines": code_lines,
                }
            )
            .eq("repo_id", repo_id)
            .execute()
        )
        return update_result.data[0] if update_result.data else None

    # Create new repository
    insert_result = (
        supabase.table("repositories")
        .insert(
            {
                "owner_id": owner_id,
                "repo_id": repo_id,
                "repo_name": repo_name,
                "created_by": user_id + ":" + user_name,
                "updated_by": user_id + ":" + user_name,
                "file_count": file_count,
                "blank_lines": blank_lines,
                "comment_lines": comment_lines,
                "code_lines": code_lines,
            }
        )
        .execute()
    )
    return insert_result.data[0] if insert_result.data else None
