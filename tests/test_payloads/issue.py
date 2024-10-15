from services.github.github_types import GitHubLabeledPayload

mock_issue_payload: GitHubLabeledPayload = {
    "action": "labeled",
    "issue": {
        "number": 1,
        "title": "Test Issue",
        "body": "This is a test issue for unit testing.",
        "user": {
            "login": "test-user",
            "id": 1
        },
    },
    "label": {
        "name": "gitauto"
    },
    "repository": {
        "name": "test-repo",
        "full_name": "test-org/test-repo",
        "owner": {
            "login": "test-org",
            "id": 1,
            "type": "Organization"
        }
    },
    "sender": {
        "login": "test-user",
        "id": 1
    },
    "installation": {
        "id": 1
    }
}