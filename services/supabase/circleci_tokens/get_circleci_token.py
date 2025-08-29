# Third-party imports
from schemas.supabase.types import CircleciTokens

# Local imports
from services.supabase.client import supabase
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def get_circleci_token(owner_id: int):
    result = (
        supabase.table("circleci_tokens")
        .select("*")
        .eq("owner_id", owner_id)
        .limit(1)
        .execute()
    )

    if result.data:
        token_data: CircleciTokens = result.data[0]
        return token_data
    return None
