from typing import cast

from services.github.types.webhook.pull_request_review import PullRequestReviewPayload
from services.webhook.utils.adapt_pr_review_to_review_payload import (
    adapt_pr_review_to_review_payload,
)


def test_adapt_pr_review_to_review_payload_maps_fields():
    payload = {
        "action": "submitted",
        "review": {
            "id": 555,
            "node_id": "PRR_555",
            "body": "Please change the target branch",
            "user": {"login": "matsutaro", "type": "User"},
            "state": "changes_requested",
        },
        "pull_request": {
            "number": 42,
            "head": {"ref": "gitauto/dashboard-20250101-Ab1C", "sha": "abc123"},
            "base": {"ref": "main"},
        },
        "repository": {"id": 1, "owner": {"login": "o"}, "name": "r"},
        "organization": {"id": 2},
        "sender": {"login": "matsutaro"},
        "installation": {"id": 3},
    }

    result = adapt_pr_review_to_review_payload(
        payload=cast(PullRequestReviewPayload, payload)
    )

    assert result is not None
    assert result["action"] == "submitted"
    assert result["comment"]["id"] == 555
    assert result["comment"]["node_id"] == "PRR_555"
    assert result["comment"]["body"] == "Please change the target branch"
    assert result["comment"]["user"] == {"login": "matsutaro", "type": "User"}
    assert result["comment"]["path"] == ""
    assert result["comment"]["subject_type"] == "pr_review"
    assert result["comment"]["line"] == 0
    assert result["comment"]["side"] == ""
    assert result["pull_request"] == payload["pull_request"]
    assert result["repository"] == payload["repository"]
    assert result["organization"] == payload["organization"]  # type: ignore[typeddict-item]
    assert result["sender"] == payload["sender"]
    assert result["installation"] == payload["installation"]


def test_adapt_pr_review_to_review_payload_no_organization():
    payload = {
        "action": "submitted",
        "review": {
            "id": 666,
            "node_id": "PRR_666",
            "body": "Looks good overall but fix the typo",
            "user": {"login": "user1", "type": "User"},
            "state": "commented",
        },
        "pull_request": {
            "number": 7,
            "head": {"ref": "gitauto/fix-20250101-Ab1C", "sha": "def456"},
            "base": {"ref": "main"},
        },
        "repository": {"id": 1, "owner": {"login": "user1"}, "name": "repo"},
        "sender": {"login": "user1"},
        "installation": {"id": 3},
    }

    result = adapt_pr_review_to_review_payload(
        payload=cast(PullRequestReviewPayload, payload)
    )

    assert result is not None
    assert result["action"] == "submitted"
    assert result["comment"]["id"] == 666
    assert "organization" not in result
    assert result["sender"] == payload["sender"]
