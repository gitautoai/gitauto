# Check conftest content
import random
import pytest
from services.github.token.get_installation_token import get_installation_access_token
from services.github.types.github_types import BaseArgs


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


@pytest.fixture
def test_token(test_installation_id):
    return get_installation_access_token(installation_id=test_installation_id)


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
        }

        # Apply any overrides
        for key, value in overrides.items():
            defaults[key] = value

        return defaults

    return _create
