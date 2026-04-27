from services.supabase.client import supabase
from services.types.base_args import Platform
from services.website.get_default_structured_rules import get_default_structured_rules
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=None, raise_on_error=False)
def insert_repository(
    *,
    platform: Platform,
    owner_id: int,
    repo_id: int,
    repo_name: str,
    user_id: int,
    user_name: str,
    file_count: int = 0,
    code_lines: int = 0,
):
    structured_rules = get_default_structured_rules()

    insert_result = (
        supabase.table("repositories")
        .insert(
            {
                "platform": platform,
                "owner_id": owner_id,
                "repo_id": repo_id,
                "repo_name": repo_name,
                "file_count": file_count,
                "code_lines": code_lines,
                "structured_rules": structured_rules,
                "created_by": str(user_id) + ":" + user_name,
                "updated_by": str(user_id) + ":" + user_name,
            }
        )
        .execute()
    )

    row = insert_result.data[0] if insert_result.data else None
    logger.info("insert_repository: inserted repo_id=%s platform=%s", repo_id, platform)
    return row
