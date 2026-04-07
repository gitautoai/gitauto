from utils.error.handle_exceptions import handle_exceptions

# Billable triggers that incur a credit charge
BILLABLE_TRIGGERS = {
    "issue_label",
    "unknown",
    "schedule",
    "dashboard",
    "manual",
    "issue_comment",
}


@handle_exceptions(default_return_value=[], raise_on_error=False)
def compare_billing_records(
    github_prs_by_repo: dict[str, list[dict]],
    usage_records: list[dict],
    credit_records: list[dict],
):
    """Cross-reference GitHub PRs (source of truth), usage, and credits.
    Every GitHub PR MUST have a usage record and a credit record unless trigger is free.
    Any mismatch means we missed charging. Returns list of mismatches."""
    mismatches = []

    # Build lookups
    usage_by_repo_pr: dict[tuple[str, int | None], list[dict]] = {}
    for u in usage_records:
        key = (u["repo_name"], u["pr_number"])
        if key not in usage_by_repo_pr:
            usage_by_repo_pr[key] = []
        usage_by_repo_pr[key].append(u)

    billable_usage_ids = {
        u["id"] for u in usage_records if u["trigger"] in BILLABLE_TRIGGERS
    }
    all_usage_ids = {u["id"] for u in usage_records}
    credit_usage_ids = {c["usage_id"] for c in credit_records if c["usage_id"]}

    github_pr_keys = set()
    for repo, prs in github_prs_by_repo.items():
        for pr in prs:
            github_pr_keys.add((repo, pr["number"]))

    # Build set of (repo, pr) that have credits via usage_id
    credited_repo_prs: set[tuple[str, int | None]] = set()
    for c in credit_records:
        if c["usage_id"]:
            for u in usage_records:
                if u["id"] == c["usage_id"]:
                    credited_repo_prs.add((u["repo_name"], u["pr_number"]))
                    break

    # Check 1: GitHub PR without any usage record
    for repo, prs in github_prs_by_repo.items():
        for pr in prs:
            key = (repo, pr["number"])
            if key not in usage_by_repo_pr:
                mismatches.append(
                    {
                        "type": "PR_NO_USAGE",
                        "detail": f"GitHub PR #{pr['number']} in {repo} has no usage record",
                    }
                )

    # Check 2: GitHub PR has billable usage but no credit (MISSED CHARGE)
    for repo, prs in github_prs_by_repo.items():
        for pr in prs:
            key = (repo, pr["number"])
            pr_usages = usage_by_repo_pr.get(key, [])
            has_billable = any(u["trigger"] in BILLABLE_TRIGGERS for u in pr_usages)
            if has_billable and key not in credited_repo_prs:
                triggers = {u["trigger"] for u in pr_usages}
                mismatches.append(
                    {
                        "type": "PR_NO_CREDIT",
                        "detail": f"GitHub PR #{pr['number']} in {repo} (triggers: {triggers}) has no credit - MISSED CHARGE",
                    }
                )

    # Check 3: Billable usage without matching GitHub PR
    seen_repo_pr: set[tuple[str, int | None]] = set()
    for u in usage_records:
        if u["trigger"] not in BILLABLE_TRIGGERS:
            continue
        key = (u["repo_name"], u["pr_number"])
        if key in seen_repo_pr:
            continue
        seen_repo_pr.add(key)
        if key not in github_pr_keys and u["pr_number"]:
            mismatches.append(
                {
                    "type": "USAGE_NO_PR",
                    "detail": f"Usage #{u['id']} ({u['repo_name']} PR #{u['pr_number']}, trigger={u['trigger']}) has no GitHub PR",
                }
            )

    # Check 4: Billable usage without credit (MISSED CHARGE)
    for uid in billable_usage_ids:
        if uid not in credit_usage_ids:
            u = next(r for r in usage_records if r["id"] == uid)
            mismatches.append(
                {
                    "type": "USAGE_NO_CREDIT",
                    "detail": f"Usage #{uid} ({u['trigger']}, {u['repo_name']} PR #{u['pr_number']}) has no credit - MISSED CHARGE",
                }
            )

    # Check 5: Credits pointing to non-existent usage (orphaned credit)
    for c in credit_records:
        if c["usage_id"] and c["usage_id"] not in all_usage_ids:
            mismatches.append(
                {
                    "type": "CREDIT_NO_USAGE",
                    "detail": f"Credit #{c['id']} points to usage #{c['usage_id']} which doesn't exist in range",
                }
            )

    # Check 6: Credits linked to free trigger usage (unexpected charge)
    for c in credit_records:
        if (
            c["usage_id"]
            and c["usage_id"] in all_usage_ids
            and c["usage_id"] not in billable_usage_ids
        ):
            u = next(r for r in usage_records if r["id"] == c["usage_id"])
            mismatches.append(
                {
                    "type": "CREDIT_FREE_TRIGGER",
                    "detail": f"Credit #{c['id']} linked to free trigger usage #{c['usage_id']} (trigger={u['trigger']})",
                }
            )

    return mismatches
