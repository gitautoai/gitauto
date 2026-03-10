# pyright: reportUnusedVariable=false

from typing import cast

from services.github.types.pull_request import PullRequest
from services.github.types.webhook.issue_comment import IssueCommentWebhookPayload
from services.webhook.utils.adapt_pr_comment_to_review_payload import (
    adapt_pr_comment_to_review_payload,
)


def test_adapt_pr_comment_to_review_payload_maps_fields():
    """Test that adapter correctly maps issue_comment fields to ReviewRunPayload shape."""
    payload = {
        "action": "created",
        "comment": {
            "id": 111,
            "node_id": "IC_111",
            "body": "fix this please",
            "user": {"login": "reviewer", "type": "User"},
            "created_at": "2025-01-01T00:00:00Z",
            "updated_at": "2025-01-01T00:00:00Z",
        },
        "issue": {
            "number": 10,
            "pull_request": {"url": "https://api.github.com/repos/o/r/pulls/10"},
        },
        "repository": {"id": 1, "owner": {"login": "o"}, "name": "r"},
        "organization": {"id": 2},
        "sender": {"login": "reviewer"},
        "installation": {"id": 3},
        "changes": {},
    }
    pr = {
        "number": 10,
        "title": "Fix bug",
        "body": "Fixes issue",
        "url": "https://api.github.com/repos/o/r/pulls/10",
        "user": {"login": "gitauto-ai[bot]"},
        "head": {"ref": "gitauto/dashboard-20250101-Ab1C", "sha": "abc123"},
        "base": {"ref": "main"},
    }

    result = adapt_pr_comment_to_review_payload(
        payload=cast(IssueCommentWebhookPayload, payload),
        pull_request=cast(PullRequest, pr),
    )

    assert result is not None
    assert result["action"] == "created"
    assert result["comment"]["id"] == 111
    assert result["comment"]["node_id"] == "IC_111"
    assert result["comment"]["body"] == "fix this please"
    assert result["comment"]["user"] == {"login": "reviewer", "type": "User"}
    assert result["comment"]["path"] == ""
    assert result["comment"]["subject_type"] == "pr_comment"
    assert result["comment"]["line"] == 0
    assert result["comment"]["side"] == ""
    assert result["pull_request"] == pr
    assert result["repository"] == payload["repository"]
    assert result["organization"] == payload["organization"]  # type: ignore[typeddict-item]
    assert result["sender"] == payload["sender"]
    assert result["installation"] == payload["installation"]


def test_adapt_pr_comment_to_review_payload_no_organization():
    """Test that adapter works for personal repos without 'organization' key."""
    payload = {
        "action": "created",
        "comment": {
            "id": 222,
            "node_id": "IC_222",
            "body": "please fix",
            "user": {"login": "user1", "type": "User"},
            "created_at": "2025-01-01T00:00:00Z",
            "updated_at": "2025-01-01T00:00:00Z",
        },
        "issue": {
            "number": 5,
            "pull_request": {"url": "https://api.github.com/repos/user1/repo/pulls/5"},
        },
        "repository": {"id": 1, "owner": {"login": "user1"}, "name": "repo"},
        "sender": {"login": "user1"},
        "installation": {"id": 3},
        "changes": {},
    }
    pr = {
        "number": 5,
        "title": "Fix bug",
        "body": "Fixes issue",
        "url": "https://api.github.com/repos/user1/repo/pulls/5",
        "user": {"login": "gitauto-ai[bot]"},
        "head": {"ref": "gitauto/fix-20250101-Ab1C", "sha": "def456"},
        "base": {"ref": "main"},
    }

    result = adapt_pr_comment_to_review_payload(
        payload=cast(IssueCommentWebhookPayload, payload),
        pull_request=cast(PullRequest, pr),
    )

    assert result is not None
    assert result["action"] == "created"
    assert result["comment"]["id"] == 222
    assert "organization" not in result
    assert result["sender"] == payload["sender"]
