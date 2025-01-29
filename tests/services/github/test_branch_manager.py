import os
from services.github.branch_manager import get_default_branch
from tests.constants import OWNER, REPO

TOKEN = os.getenv("GH_APP_TOKEN")


def test_get_default_branch() -> None:
    # Exercise
    default_branch, commit_sha = get_default_branch(OWNER, REPO, TOKEN)

    # Verify
    assert default_branch == "main"
    assert len(commit_sha) == 40
