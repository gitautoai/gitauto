# Standard imports
from typing import cast

# Third party imports
import requests

# Local imports
from config import GITHUB_API_URL, TIMEOUT
from services.github.types.branch_protection import BranchProtection
from services.github.utils.create_headers import create_headers
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def get_required_status_checks(owner: str, repo: str, branch: str, token: str):
    """https://docs.github.com/en/rest/branches/branch-protection#get-branch-protection"""
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/branches/{branch}/protection"
    headers = create_headers(token=token)
    response = requests.get(url=url, headers=headers, timeout=TIMEOUT)

    # NOTE: 403 happens when GitHub App lacks "Administration: Read" permission
    if response.status_code == 403:
        print(f"No permission to read branch protection for {owner}/{repo}/{branch}")
        return None

    if response.status_code == 404:
        print(f"No branch protection configured for {owner}/{repo}/{branch}")
        return None

    response.raise_for_status()
    protection = cast(BranchProtection, response.json())
    required_status_checks = protection.get("required_status_checks")

    if not required_status_checks:
        print(
            f"Branch protection exists but no required status checks configured for {owner}/{repo}/{branch}"
        )
        return None

    contexts = set(required_status_checks.get("contexts", []))
    checks = {
        check.get("context") for check in required_status_checks.get("checks", [])
    }

    return list(contexts | checks)
