# Standard imports
from typing import cast

# Third-party imports
from schemas.supabase.types import Owners

# Local imports
from services.supabase.client import supabase
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def get_owner(owner_id: int):
    result = supabase.table("owners").select("*").eq("owner_id", owner_id).execute()
    if not result.data:
        return None

    return cast(Owners, result.data[0])
