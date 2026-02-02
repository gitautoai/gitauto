# flake8: noqa: E402
# pylint: disable=wrong-import-position
import os
import random

os.environ.setdefault("GITAUTO_API_KEY", "test-api-key")

import pytest
from services.git.git_clone_to_efs import clone_tasks
from services.github.token.get_installation_token import get_installation_access_token
from services.github.types.github_types import BaseArgs


@pytest.fixture(autouse=True)
def clear_clone_tasks():
    """Clear clone_tasks dict after each test to prevent subprocess cleanup warnings."""
    yield
    clone_tasks.clear()


# Test constants as fixtures
@pytest.fixture
def test_owner():
    return "gitautoai"


@pytest.fixture
def test_repo():
    return "gitauto"


@pytest.fixture
def test_forked_repo():
    return "DeepSeek-R1"


@pytest.fixture
def test_installation_id():
    return 60314628


# Session scope to avoid GitHub API rate limiting on CI - 1 call per run, not per test
@pytest.fixture(scope="session")
def test_token():
    return get_installation_access_token(installation_id=60314628)


# Helper function as fixture - returns a function that can be called with overrides
@pytest.fixture
def create_test_base_args():
    def _create(**overrides) -> BaseArgs:
        defaults: BaseArgs = {
            "input_from": "github",
            "owner_type": "User",
            "owner_id": random.randint(1, 999999),
            "owner": "test-owner",
            "repo_id": random.randint(1, 999999),
            "repo": "test-repo",
            "clone_url": "https://github.com/test-owner/test-repo.git",
            "is_fork": False,
            "issue_number": random.randint(1, 9999),
            "issue_title": "Test Issue",
            "issue_body": "Test issue body",
            "issue_comments": [],
            "latest_commit_sha": "abc123",
            "issuer_name": "test-user",
            "base_branch": "main",
            "new_branch": "test-branch",
            "installation_id": random.randint(1, 999999),
            "token": "test-token",
            "sender_id": random.randint(1, 999999),
            "sender_name": "test-sender",
            "sender_email": "test@example.com",
            "is_automation": False,
            "reviewers": [],
            "github_urls": [],
            "other_urls": [],
            "clone_dir": "/tmp/test-owner/test-repo/pr-123",
        }

        # Apply any overrides
        for key, value in overrides.items():
            defaults[key] = value

        return defaults

    return _create
