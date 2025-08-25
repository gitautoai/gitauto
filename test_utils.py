"""Test utilities for creating test data."""


def create_test_base_args(**overrides):
    """Helper function to create valid BaseArgs dictionary for testing."""
    default_args = {
        "input_from": "github",
        "owner_type": "User",
        "owner_id": 123456,
        "owner": "test_owner",
        "repo_id": 789012,
        "repo": "test_repo",
        "clone_url": "https://github.com/test_owner/test_repo.git",
        "is_fork": False,
        "issue_number": 1,
        "issue_title": "Test Issue",
        "issue_body": "Test issue body",
        "issue_comments": [],
        "latest_commit_sha": "abc123",
        "issuer_name": "test_issuer",
        "base_branch": "main",
        "new_branch": "feature/test-branch",
        "installation_id": 12345,
        "token": "test_token_123",
        "sender_id": 67890,
        "sender_name": "test_sender",
        "sender_email": "test@example.com",
        "is_automation": False,
        "reviewers": [],
        "github_urls": [],
        "other_urls": [],
    }
    default_args.update(overrides)
    return default_args
