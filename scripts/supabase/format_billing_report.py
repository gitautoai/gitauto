from scripts.supabase.compare_billing_records import BILLABLE_TRIGGERS
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value="", raise_on_error=False)
def format_billing_report(
    owner: str,
    repos: list[str],
    github_prs_by_repo: dict[str, list[dict]],
    usage_records: list[dict],
    credit_records: list[dict],
    mismatches: list[dict],
    start: str,
    end: str,
):
    """Format the billing consistency check report for Slack/stdout."""
    total_github_prs = sum(len(prs) for prs in github_prs_by_repo.values())
    billable_usage = [u for u in usage_records if u["trigger"] in BILLABLE_TRIGGERS]
    free_usage = [u for u in usage_records if u["trigger"] not in BILLABLE_TRIGGERS]
    total_credits = len(credit_records)

    lines = [
        f"{owner} Billing Consistency ({start} to {end})",
        f"GitHub PRs: {total_github_prs} | Billable usage: {len(billable_usage)} | Free usage: {len(free_usage)} | Credits: {total_credits}",
        "",
    ]

    if not mismatches:
        lines.append("All records match.")
    else:
        lines.append(f"{len(mismatches)} mismatch(es) found:")
        for m in mismatches:
            lines.append(f"  - [{m['type']}] {m['detail']}")

    lines.append("")
    lines.append("Per-repo breakdown:")
    for repo in sorted(repos):
        gh_count = len(github_prs_by_repo.get(repo, []))
        repo_usages = [u for u in usage_records if u["repo_name"] == repo]
        billable = len([u for u in repo_usages if u["trigger"] in BILLABLE_TRIGGERS])
        repo_usage_ids = {u["id"] for u in repo_usages}
        credits_count = len(
            [c for c in credit_records if c["usage_id"] in repo_usage_ids]
        )
        status = "OK" if billable == credits_count else "MISMATCH"
        lines.append(
            f"  {repo}: GH={gh_count} billable={billable} credits={credits_count} total_usage={len(repo_usages)} [{status}]"
        )

    return "\n".join(lines)
