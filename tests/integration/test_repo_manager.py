import os
import pytest

from services.github.repo_manager import is_repo_forked
from tests/constants import OWNER, REPO, FORKED_REPO

GH_APP_TOKEN = os.getenv("GH_APP_TOKEN")

@pytest.mark.skipif(GH_APP_TOKEN is None, reason="GH_APP_TOKEN not set")
def test_non_forked_repo():
    result = is_repo_forked(OWNER, REPO, GH_APP_TOKEN)
    assert result is False

@pytest.mark.skipif(GH_APP_TOKEN is None, reason="GH_APP_TOKEN not set")
def test_forked_repo():
    result = is_repo_forked(OWNER, FORKED_REPO, GH_APP_TOKEN)
    assert result is True
