# pylint: disable=wrong-import-position,wrong-import-order
# ruff: noqa: E402
import os
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

# Daily report must always target PROD. Locally `.env` provides SUPABASE_URL_PRD alongside a dev SUPABASE_URL — override here so services.supabase.client picks up prod. In GitHub Actions SUPABASE_URL is already prod via secrets and SUPABASE_URL_PRD is absent, so the conditionals are no-ops there.
load_dotenv()
if os.environ.get("SUPABASE_URL_PRD"):
    os.environ["SUPABASE_URL"] = os.environ["SUPABASE_URL_PRD"]
if os.environ.get("SUPABASE_SERVICE_ROLE_KEY_PRD"):
    os.environ["SUPABASE_SERVICE_ROLE_KEY"] = os.environ[
        "SUPABASE_SERVICE_ROLE_KEY_PRD"
    ]

from services.aws.get_enabled_schedules import get_enabled_schedules
from services.slack.slack_notify import slack_notify
from services.supabase.client import supabase
from services.supabase.resolve_repo_keys import resolve_repo_keys
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger

PT = ZoneInfo("America/Los_Angeles")


@handle_exceptions(default_return_value=None, raise_on_error=False)
def generate_daily_usage_report():
    """Query last 24h usage/credits/llm_requests, format by scheduled repos, post to Slack."""
    now = datetime.now(tz=timezone.utc)
    twenty_four_hours_ago = (now - timedelta(hours=24)).isoformat()
    logger.info("Daily usage report window starts at %s", twenty_four_hours_ago)

    # Base: enabled AWS EventBridge schedules
    repo_keys = get_enabled_schedules()
    scheduled_repos = resolve_repo_keys(repo_keys)

    # Usage rows in the last 24 hours
    usage_result = (
        supabase.table("usage")
        .select("id, owner_id, owner_name, repo_name, pr_number")
        .gte("created_at", twenty_four_hours_ago)
        .execute()
    )
    usage_rows = usage_result.data or []
    usage_ids = [row["id"] for row in usage_rows]
    logger.debug("Loaded %d usage rows", len(usage_rows))

    # Revenue: paid inflows in window (purchases + auto_reload top-ups)
    revenue_result = (
        supabase.table("credits")
        .select("owner_id, amount_usd")
        .in_("transaction_type", ["purchase", "auto_reload"])
        .gte("created_at", twenty_four_hours_ago)
        .execute()
    )
    revenue_by_owner_id: dict[int, int] = {}
    for row in revenue_result.data or []:
        owner_id = row["owner_id"]
        revenue_by_owner_id[owner_id] = revenue_by_owner_id.get(owner_id, 0) + int(
            row["amount_usd"]
        )

    # Cost: our LLM spend for usage rows in window
    cost_by_usage_id: dict[int, float] = {}
    if usage_ids:
        logger.info("Fetching llm_requests for %d usage ids", len(usage_ids))
        llm_result = (
            supabase.table("llm_requests")
            .select("usage_id, total_cost_usd")
            .in_("usage_id", usage_ids)
            .execute()
        )
        for row in llm_result.data or []:
            uid = row["usage_id"]
            if uid is None:
                logger.warning("llm_requests row has no usage_id; skipping")
                continue
            cost_by_usage_id[uid] = cost_by_usage_id.get(uid, 0.0) + float(
                row["total_cost_usd"]
            )
    else:
        logger.info("No usage rows in window; skipping llm_requests fetch")

    # Group by (owner_name, repo_name): dedupe PRs, count runs per PR, attribute cost
    repo_usage: dict[tuple[str, str], dict] = {}
    for row in usage_rows:
        key = (row["owner_name"], row["repo_name"])
        if key not in repo_usage:
            logger.debug("init repo_usage for %s/%s", key[0], key[1])
            repo_usage[key] = {
                "owner_id": row["owner_id"],
                "pr_runs": {},
                "pr_cost": {},
                "no_pr_count": 0,
                "no_pr_cost": 0.0,
            }
        cost = cost_by_usage_id.get(row["id"], 0.0)
        pr_num = row["pr_number"]
        if pr_num and pr_num > 0:
            logger.debug("PR run %s in %s/%s", pr_num, key[0], key[1])
            repo_usage[key]["pr_runs"][pr_num] = (
                repo_usage[key]["pr_runs"].get(pr_num, 0) + 1
            )
            repo_usage[key]["pr_cost"][pr_num] = (
                repo_usage[key]["pr_cost"].get(pr_num, 0.0) + cost
            )
        else:
            logger.debug("no-PR run in %s/%s", key[0], key[1])
            repo_usage[key]["no_pr_count"] += 1
            repo_usage[key]["no_pr_cost"] += cost

    # All repos: scheduled + any with usage
    all_keys = set(scheduled_repos.keys()) | set(repo_usage.keys())

    # Group by owner
    by_owner: dict[str, list[tuple[str, str]]] = {}
    for key in all_keys:
        by_owner.setdefault(key[0], []).append(key)

    # Totals
    total_unique_prs = sum(len(u["pr_runs"]) for u in repo_usage.values())
    total_runs = sum(
        sum(u["pr_runs"].values()) + u["no_pr_count"] for u in repo_usage.values()
    )
    total_cost = sum(cost_by_usage_id.values())
    total_revenue = sum(revenue_by_owner_id.values())
    no_pr_cost_total = sum(
        u["no_pr_cost"]
        for u in repo_usage.values()
        if u["no_pr_count"] > 0 and not u["pr_runs"]
    )

    # Format Slack message — PT date so header isn't ambiguous
    date_str = now.astimezone(PT).strftime("%Y-%m-%d")
    margin_str = (
        f"{(total_revenue - total_cost) / total_revenue * 100:.1f}%"
        if total_revenue > 0
        else "N/A"
    )
    lines = [
        f"Daily Usage Report ({date_str} PT)",
        f"Revenue: ${total_revenue}  |  Cost: ${total_cost:.2f}  |  Margin: {margin_str}",
        f"{total_unique_prs} PRs / {total_runs} runs",
    ]
    if no_pr_cost_total > 0:
        logger.info("Adding <!channel> alert: $%.2f no-PR cost", no_pr_cost_total)
        lines.append(
            f"  <!channel> ${no_pr_cost_total:.2f} cost from repos with usage but no PRs"
        )
    lines.append("")

    for owner_name in sorted(by_owner):
        keys = sorted(by_owner[owner_name], key=lambda k: k[1])
        owner_id = next(
            (repo_usage[k]["owner_id"] for k in keys if k in repo_usage),
            None,
        )
        owner_revenue = revenue_by_owner_id.get(owner_id, 0) if owner_id else 0
        owner_unique_prs = sum(
            len(repo_usage.get(k, {}).get("pr_runs", {})) for k in keys
        )
        owner_runs = sum(
            sum(repo_usage.get(k, {}).get("pr_runs", {}).values())
            + repo_usage.get(k, {}).get("no_pr_count", 0)
            for k in keys
        )
        owner_cost = sum(
            sum(repo_usage.get(k, {}).get("pr_cost", {}).values())
            + repo_usage.get(k, {}).get("no_pr_cost", 0.0)
            for k in keys
        )
        lines.append(
            f"*{owner_name}*  Revenue: ${owner_revenue}  Cost: ${owner_cost:.2f}  "
            f"({owner_unique_prs} PRs / {owner_runs} runs)"
        )

        for key in keys:
            repo_name = key[1]
            usage = repo_usage.get(key)

            if usage and usage["pr_runs"]:
                logger.debug("fmt %s/%s (PRs)", key[0], repo_name)
                repo_cost = sum(usage["pr_cost"].values()) + usage["no_pr_cost"]
                pr_parts = []
                for pr_num in sorted(usage["pr_runs"]):
                    runs = usage["pr_runs"][pr_num]
                    pr_cost = usage["pr_cost"][pr_num]
                    suffix = f" ({runs}×)" if runs > 1 else ""
                    pr_parts.append(f"#{pr_num}{suffix} ${pr_cost:.2f}")
                lines.append(
                    f"  {repo_name}  Cost: ${repo_cost:.2f}  {', '.join(pr_parts)}"
                )
            elif usage and usage["no_pr_count"] > 0:
                logger.debug("fmt %s/%s (no-PR only)", key[0], repo_name)
                lines.append(
                    f"  {repo_name} ({usage['no_pr_count']} runs, no PR) "
                    f"Cost: ${usage['no_pr_cost']:.2f}"
                )
            else:
                logger.debug("fmt %s/%s (scheduled, no usage)", key[0], repo_name)
                lines.append(f"  {repo_name} --")
        lines.append("")

    message = "\n".join(lines)
    logger.info(
        "Daily usage report: %d PRs, %d runs, revenue $%d, cost $%.2f",
        total_unique_prs,
        total_runs,
        total_revenue,
        total_cost,
    )
    logger.info("Daily usage report body:\n%s", message)
    slack_notify(message)
    logger.debug("slack_notify dispatched")
    return {
        "prs": total_unique_prs,
        "runs": total_runs,
        "revenue_usd": total_revenue,
        "cost_usd": total_cost,
    }


if __name__ == "__main__":
    result = generate_daily_usage_report()
    print(f"Report sent: {result}")  # noqa: T201
