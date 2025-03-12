# Standard imports
from supabase import Client, create_client

# Local imports
from config import SUPABASE_SERVICE_ROLE_KEY, SUPABASE_URL
from utils.handle_exceptions import handle_exceptions

# Initialize Supabase client
supabase: Client = create_client(
    supabase_url=SUPABASE_URL, supabase_key=SUPABASE_SERVICE_ROLE_KEY
)


@handle_exceptions(default_return_value=None, raise_on_error=False)
def create_or_update_repository(
    owner_id: int,
    repo_id: int,
    repo_name: str,
    created_by: str,
    updated_by: str,
    file_count: int = 0,
    blank_lines: int = 0,
    comment_lines: int = 0,
    code_lines: int = 0,
):
    # Check if repository already exists
    result = supabase.table("repositories").select("*").eq("repo_id", repo_id).execute()

    if result.data:
        # Update existing repository
        update_result = (
            supabase.table("repositories")
            .update(
                {
                    "updated_by": updated_by,
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
                "created_by": created_by,
                "updated_by": updated_by,
                "file_count": file_count,
                "blank_lines": blank_lines,
                "comment_lines": comment_lines,
                "code_lines": code_lines,
            }
        )
        .execute()
    )
    return insert_result.data[0] if insert_result.data else None
