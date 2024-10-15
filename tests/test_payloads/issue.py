from services.github.github_types import GitHubLabeledPayload

mock_issue_payload: GitHubLabeledPayload = {
    "action": "labeled",
    "issue": {
        "number": 1,
        "title": "Add type-hinting where possible in python code",
        "body": "Add type-hinting where possible in python function definitions in python code.",
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
