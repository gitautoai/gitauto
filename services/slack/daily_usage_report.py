from datetime import datetime, timedelta, timezone

from services.aws.get_enabled_schedules import get_enabled_schedules
from services.slack.slack_notify import slack_notify
from services.supabase.client import supabase
from services.supabase.resolve_repo_keys import resolve_repo_keys
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=None, raise_on_error=False)
def generate_daily_usage_report():
    """Query last 24h usage/credits, format by scheduled repos, post to Slack."""
    now = datetime.now(tz=timezone.utc)
    twenty_four_hours_ago = (now - timedelta(hours=24)).isoformat()

    # Base: enabled AWS EventBridge schedules
    repo_keys = get_enabled_schedules()
    scheduled_repos = resolve_repo_keys(repo_keys)

    # Get all usage records in the last 24 hours
    usage_result = (
        supabase.table("usage")
        .select("id, owner_name, repo_name, pr_number")
        .gte("created_at", twenty_four_hours_ago)
        .execute()
    )
    usage_rows = usage_result.data or []

    # Get credit deductions in the last 24 hours
    credit_result = (
        supabase.table("credits")
        .select("usage_id, amount_usd")
        .eq("transaction_type", "usage")
        .gte("created_at", twenty_four_hours_ago)
        .execute()
    )

    # Build map of usage_id -> absolute dollar amount
    cost_by_usage_id: dict[int, int] = {}
    for credit in credit_result.data or []:
        if credit["usage_id"] is not None:
            cost_by_usage_id[credit["usage_id"]] = abs(int(credit["amount_usd"]))

    # Group usage by (owner_name, repo_name)
    repo_usage: dict[tuple[str, str], dict] = {}
    for row in usage_rows:
        key = (row["owner_name"], row["repo_name"])
        if key not in repo_usage:
            repo_usage[key] = {"prs": [], "no_pr_count": 0, "cost": 0}
        cost = cost_by_usage_id.get(row["id"], 0)
        repo_usage[key]["cost"] += cost
        if row["pr_number"] and row["pr_number"] > 0:
            repo_usage[key]["prs"].append(row["pr_number"])
        else:
            repo_usage[key]["no_pr_count"] += 1

    # All repos: scheduled + any with usage
    all_keys = set(scheduled_repos.keys()) | set(repo_usage.keys())

    # Group by owner
    by_owner: dict[str, list[tuple[str, str]]] = {}
    for key in all_keys:
        owner_name = key[0]
        if owner_name not in by_owner:
            by_owner[owner_name] = []
        by_owner[owner_name].append(key)

    # Calculate totals
    total_prs = sum(len(u["prs"]) for u in repo_usage.values())
    total_credits_usd = sum(abs(int(c["amount_usd"])) for c in credit_result.data or [])
    no_pr_usd = sum(
        u["cost"] for u in repo_usage.values() if u["no_pr_count"] > 0 and not u["prs"]
    )

    # Format Slack message
    date_str = now.strftime("%Y-%m-%d")
    lines = [
        f"Daily Usage Report ({date_str})",
        f"Total: {total_prs} PRs, ${total_credits_usd}",
    ]
    if no_pr_usd > 0:
        lines.append(f"  <!channel> ${no_pr_usd} from usage without PRs")
    lines.append("")

    for owner_name in sorted(by_owner):
        keys = sorted(by_owner[owner_name], key=lambda k: k[1])
        owner_prs = sum(len(repo_usage.get(k, {}).get("prs", [])) for k in keys)
        owner_cost = sum(repo_usage.get(k, {}).get("cost", 0) for k in keys)
        lines.append(f"*{owner_name}* ({owner_prs} PRs, ${owner_cost})")

        for key in keys:
            repo_name = key[1]
            usage = repo_usage.get(key)

            if usage and usage["prs"]:
                pr_list = ", ".join(f"#{pr}" for pr in sorted(usage["prs"]))
                lines.append(f"  {repo_name} {pr_list}")
            elif usage and usage["no_pr_count"] > 0:
                lines.append(f"  {repo_name} ({usage['no_pr_count']} runs, no PR)")
            else:
                lines.append(f"  {repo_name} --")
        lines.append("")

    message = "\n".join(lines)
    logger.info("Daily usage report: %d PRs, $%d", total_prs, total_credits_usd)
    slack_notify(message)

    return {"prs": total_prs, "total_usd": total_credits_usd}


if __name__ == "__main__":
    result = generate_daily_usage_report()
    print(f"Report sent: {result}")  # noqa: T201
