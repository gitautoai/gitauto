from services.github.branch_manager import get_default_branch
from services.github.github_manager import get_installation_access_token
from tests.constants import INSTALLATION_ID, OWNER, REPO


def test_get_default_branch() -> None:
    # Setup
    token = get_installation_access_token(installation_id=INSTALLATION_ID)

    # Exercise
    default_branch, commit_sha = get_default_branch(OWNER, REPO, token)

    # Verify
    assert default_branch == "main"
    assert len(commit_sha) == 40
