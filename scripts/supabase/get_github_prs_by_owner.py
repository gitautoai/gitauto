import requests

from config import GITHUB_API_URL, TIMEOUT
from services.github.utils.create_headers import create_headers
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value={}, raise_on_error=False)
def get_github_prs_by_owner(token, owner, repos, start, end):
    """Get all GitAuto PRs across repos for an owner in date range. Returns dict of repo -> list of PRs."""
    headers = create_headers(token=token)
    prs_by_repo = {}

    for repo in sorted(repos):
        repo_prs = []
        for state in ["open", "closed"]:
            response = requests.get(
                f"{GITHUB_API_URL}/repos/{owner}/{repo}/pulls",
                headers=headers,
                params={
                    "state": state,
                    "per_page": 100,
                    "sort": "created",
                    "direction": "desc",
                },
                timeout=TIMEOUT,
            )
            if response.status_code != 200:
                print(
                    f"  GitHub API error for {repo} ({state}): {response.status_code}"
                )
                continue
            data = response.json()
            if not isinstance(data, list):
                continue
            for pr in data:
                if pr["user"]["login"] != "gitauto-ai[bot]":
                    continue
                created = pr["created_at"][:10]
                if created < start or created > end:
                    continue
                repo_prs.append(
                    {
                        "number": pr["number"],
                        "state": pr["state"],
                        "created_at": pr["created_at"],
                        "title": pr["title"],
                    }
                )
        if repo_prs:
            prs_by_repo[repo] = repo_prs
        print(f"  {repo}: {len(repo_prs)} PRs")

    return prs_by_repo
