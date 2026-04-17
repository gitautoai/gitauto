from services.supabase.client import supabase
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=0.0, raise_on_error=False)
def get_total_cost_for_pr(owner_name: str, repo_name: str, pr_number: int):
    # Get all usage IDs for this PR
    usage_result = (
        supabase.table("usage")
        .select("id")
        .eq("owner_name", owner_name)
        .eq("repo_name", repo_name)
        .eq("pr_number", pr_number)
        .execute()
    )
    if not usage_result.data:
        logger.info("No usage records for %s/%s#%d", owner_name, repo_name, pr_number)
        return 0.0

    usage_ids = [row["id"] for row in usage_result.data]

    # Sum LLM costs across all invocations for this PR
    cost_result = (
        supabase.table("llm_requests")
        .select("total_cost_usd")
        .in_("usage_id", usage_ids)
        .execute()
    )
    total = (
        sum(row["total_cost_usd"] for row in cost_result.data)
        if cost_result.data
        else 0.0
    )
    logger.info(
        "Total LLM cost for %s/%s#%d: $%.4f (%d usage records, %d llm_requests)",
        owner_name,
        repo_name,
        pr_number,
        total,
        len(usage_ids),
        len(cost_result.data) if cost_result.data else 0,
    )
    return total
