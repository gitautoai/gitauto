# Standard imports
from typing import cast

# Third-party imports
from schemas.supabase.types import Repositories

# Local imports
from services.supabase.client import supabase
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def get_repository(owner_id: int, repo_id: int):
    # Query by both owner_id and repo_id because stale entries can exist after repo transfers.
    # When a repo is transferred (e.g., mohavro -> DashFin), the old owner's entry may remain
    # while the new owner's entry is created. Without owner_id, we might return the wrong settings.
    result = (
        supabase.table("repositories")
        .select("*")
        .eq("owner_id", owner_id)
        .eq("repo_id", repo_id)
        .maybe_single()
        .execute()
    )

    if result and result.data:
        return cast(Repositories, result.data)

    return None
