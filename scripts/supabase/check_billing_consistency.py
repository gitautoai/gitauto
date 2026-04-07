#!/usr/bin/env python3
# flake8: noqa: E402
# pylint: disable=wrong-import-position
"""Check billing consistency between GitHub PRs, usage table, and credits table.

Source of truth: GitHub PRs created by gitauto-ai[bot].
All three MUST perfectly match - any mismatch means we missed charging.
Targets all owners who have purchased credits. Accepts date range, default 1 month based on created_at.

Usage:
  python3 scripts/supabase/check_billing_consistency.py
  python3 scripts/supabase/check_billing_consistency.py --start 2026-03-01 --end 2026-04-01
  python3 scripts/supabase/check_billing_consistency.py --owner Foxquilt
"""

import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

import requests

# Add repo root to Python path so imports work
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from scripts.github.get_installation_token import get_installation_token
from scripts.supabase.compare_billing_records import compare_billing_records
from scripts.supabase.format_billing_report import format_billing_report
from scripts.supabase.get_github_prs_by_owner import get_github_prs_by_owner
from services.slack.slack_notify import slack_notify
from services.supabase.credits.get_credit_records_by_owner import (
    get_credit_records_by_owner,
)
from services.supabase.usage.get_usage_records_by_owner import (
    get_usage_records_by_owner,
)


def main():
    parser = argparse.ArgumentParser(
        description="Check billing consistency for credit-based owners"
    )
    now = datetime.now(tz=timezone.utc)
    default_start = (now - timedelta(days=30)).strftime("%Y-%m-%d")
    default_end = (now + timedelta(days=1)).strftime("%Y-%m-%d")

    parser.add_argument(
        "--start", default=default_start, help=f"Start date (default: {default_start})"
    )
    parser.add_argument(
        "--end", default=default_end, help=f"End date (default: {default_end})"
    )
    parser.add_argument(
        "--owner",
        default=None,
        help="Check specific owner only (default: all credit owners)",
    )
    args = parser.parse_args()

    print(f"Checking billing consistency from {args.start} to {args.end}")

    # Credit-based owners and their repos (hardcoded for now)
    all_owners = [
        {
            "owner_id": 28540514,
            "owner_name": "Foxquilt",
            "repos": [
                "foxcom-forms",
                "foxcom-forms-backend",
                "foxcom-payment-backend",
                "foxcom-payment-frontend",
                "foxden-admin-portal",
                "foxden-admin-portal-backend",
                "foxden-auth-service",
                "foxden-billing",
                "foxden-policy-document-backend",
                "foxden-rating-quoting-backend",
                "foxden-shared-lib",
                "foxden-tools",
                "foxden-version-controller",
                "foxden-version-controller-client",
            ],
        },
    ]

    if args.owner:
        owners = [o for o in all_owners if o["owner_name"] == args.owner]
        if not owners:
            print(f"Error: Owner '{args.owner}' not in hardcoded list")
            sys.exit(1)
    else:
        owners = all_owners

    print(f"Owners to check: {', '.join(o['owner_name'] for o in owners)}")

    all_reports = []
    has_mismatches = False

    for owner in owners:
        owner_name = owner["owner_name"]
        owner_id = owner["owner_id"]
        print(f"\n--- {owner_name} (owner_id={owner_id}) ---")

        # Get GitHub token for this owner
        try:
            token = get_installation_token(owner_name)
        except (ValueError, requests.HTTPError) as e:
            print(f"  Skipping {owner_name}: {e}")
            continue

        repos = owner["repos"]

        # Query all three data sources
        github_prs_by_repo = get_github_prs_by_owner(
            token, owner_name, repos, args.start, args.end
        )
        usage_records = get_usage_records_by_owner(owner_name, args.start, args.end)
        credit_records = get_credit_records_by_owner(owner_id, args.start, args.end)
        print(f"  Usage: {len(usage_records)}, Credits: {len(credit_records)}")

        # Compare and report
        mismatches = compare_billing_records(
            github_prs_by_repo, usage_records, credit_records
        )
        report = format_billing_report(
            owner_name,
            repos,
            github_prs_by_repo,
            usage_records,
            credit_records,
            mismatches,
            args.start,
            args.end,
        )
        print("\n" + report)
        all_reports.append(report)

        if mismatches:
            has_mismatches = True

    # Slack notification with combined report
    full_report = "\n\n".join(all_reports)
    slack_notify(text=full_report)

    if has_mismatches:
        sys.exit(1)


if __name__ == "__main__":
    main()
