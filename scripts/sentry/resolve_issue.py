import argparse
import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv()


def resolve_sentry_issue(issue_id: str, headers: dict, sentry_org: str):
    url = f"https://sentry.io/api/0/organizations/{sentry_org}/issues/{issue_id}/"
    payload = {"status": "resolved"}

    print(f"Resolving {issue_id}...", end=" ")
    response = requests.put(url, headers=headers, json=payload, timeout=30)

    if response.status_code == 200:
        print("done")
    else:
        print(f"failed (HTTP {response.status_code})")
        return False
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Resolve Sentry issues")
    parser.add_argument(
        "issue_ids", nargs="+", help="Sentry issue IDs (e.g., AGENT-229 AGENT-22A)"
    )

    args = parser.parse_args()

    sentry_token = os.getenv("SENTRY_PERSONAL_TOKEN")
    sentry_org = os.getenv("SENTRY_ORG_SLUG")

    if not sentry_token or not sentry_org:
        print("Error: SENTRY_PERSONAL_TOKEN and SENTRY_ORG_SLUG must be set in .env")
        sys.exit(1)

    headers = {
        "Authorization": f"Bearer {sentry_token}",
        "Content-Type": "application/json",
    }

    failed = []
    for issue_id in args.issue_ids:
        if not resolve_sentry_issue(issue_id, headers, sentry_org):
            failed.append(issue_id)

    if failed:
        print(f"\nFailed to resolve: {', '.join(failed)}")
        sys.exit(1)
