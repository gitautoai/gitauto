import os
import pytest

from tests.constants import OWNER, REPO, FORKED_REPO
from services.github.repo_manager import is_repo_forked

GH_APP_TOKEN = os.getenv("GH_APP_TOKEN")
if not GH_APP_TOKEN:
    pytest.skip("GH_APP_TOKEN not set", allow_module_level=True)


def test_is_repo_forked_non_forked():
    # Test with a non-forked repository
    result = is_repo_forked(owner=OWNER, repo=REPO, token=GH_APP_TOKEN)
    assert result is False
 
def test_is_repo_forked_forked():
    # Test with a forked repository
    result = is_repo_forked(owner=OWNER, repo=FORKED_REPO, token=GH_APP_TOKEN)
    assert result is True
