import random
from services.github.types.github_types import BaseArgs


def create_test_base_args(**overrides):
    """Create a BaseArgs object for testing with sensible defaults."""
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
