from services.supabase.client import supabase
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value={}, raise_on_error=False)
def resolve_repo_keys(repo_keys: set[tuple[int, int]]):
    """Resolve (owner_id, repo_id) to (owner_name, repo_name) dict."""
    if not repo_keys:
        return {}

    owner_ids = list({k[0] for k in repo_keys})
    repo_ids = list({k[1] for k in repo_keys})

    owners_result = (
        supabase.table("owners")
        .select("owner_id, owner_name")
        .in_("owner_id", owner_ids)
        .execute()
    )
    owner_id_to_name: dict[int, str] = {
        o["owner_id"]: o["owner_name"] for o in owners_result.data or []
    }

    repos_result = (
        supabase.table("repositories")
        .select("owner_id, repo_id, repo_name")
        .in_("repo_id", repo_ids)
        .execute()
    )

    result: dict[tuple[str, str], None] = {}
    for repo in repos_result.data or []:
        key = (repo["owner_id"], repo["repo_id"])
        if key in repo_keys:
            owner_name = owner_id_to_name.get(repo["owner_id"], str(repo["owner_id"]))
            result[(owner_name, repo["repo_name"])] = None
    return result
