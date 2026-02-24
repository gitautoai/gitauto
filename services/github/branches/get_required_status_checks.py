# Standard imports
from dataclasses import dataclass
from typing import cast

# Third party imports
import requests

# Local imports
from config import GITHUB_API_URL, TIMEOUT
from services.github.types.branch_protection import BranchProtection
from services.github.utils.create_headers import create_headers
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@dataclass
class StatusChecksResult:
    status_code: int = 201
    checks: list[str] | None = None
    strict: bool = True


@handle_exceptions(default_return_value=StatusChecksResult(), raise_on_error=False)
def get_required_status_checks(owner: str, repo: str, branch: str, token: str):
    """https://docs.github.com/en/rest/branches/branch-protection#get-branch-protection"""
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/branches/{branch}/protection"
    headers = create_headers(token=token)
    response = requests.get(url=url, headers=headers, timeout=TIMEOUT)

    # NOTE: 403 happens when GitHub App lacks "Administration: Read" permission
    if response.status_code == 403:
        strict = True
        logger.warning(
            "No permission to read branch protection for %s/%s/%s, assuming strict=%s",
            owner,
            repo,
            branch,
            strict,
        )
        return StatusChecksResult(status_code=403, checks=None, strict=strict)

    if response.status_code == 404:
        strict = False
        logger.warning(
            "No branch protection configured for %s/%s/%s, assuming strict=%s",
            owner,
            repo,
            branch,
            strict,
        )
        return StatusChecksResult(status_code=404, checks=[], strict=strict)

    response.raise_for_status()
    protection = cast(BranchProtection, response.json())
    required_status_checks = protection.get("required_status_checks")

    if not required_status_checks:
        logger.info(
            "Branch protection exists but no required status checks configured for %s/%s/%s",
            owner,
            repo,
            branch,
        )
        return StatusChecksResult(status_code=200, checks=[], strict=False)

    strict = required_status_checks.get("strict", False)
    contexts = set(required_status_checks.get("contexts", []))
    checks = {
        check.get("context") for check in required_status_checks.get("checks", [])
    }

    return StatusChecksResult(
        status_code=200, checks=list(contexts | checks), strict=strict
    )
