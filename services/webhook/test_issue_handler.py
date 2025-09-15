import inspect
from typing import cast
from unittest.mock import patch
from services.webhook.issue_handler import create_pr_from_issue
from services.github.types.github_types import GitHubLabeledPayload


def test_create_pr_from_issue_wrong_label_early_return():
    """Test early return when wrong label is provided"""
    payload_dict = {
        "action": "labeled",
        "label": {"name": "wrong-label"},  # Not "gitauto"
        "issue": {"number": 123, "title": "Test Issue"},
        "repository": {"name": "test_repo"},
    }
    payload = cast(GitHubLabeledPayload, payload_dict)

    lambda_info: dict[str, str | None] = {
        "log_group": "test",
        "log_stream": "test",
        "request_id": "test",
    }

    # Function should complete without errors (early return due to wrong label)
    create_pr_from_issue(
        payload=payload,
        trigger="issue_label",
        input_from="github",
        lambda_info=lambda_info,
    )


@patch("services.webhook.issue_handler.create_user_request")
def test_lambda_info_parameter_exists(mock_create_user_request):
    """Test that the create_pr_from_issue function accepts lambda_info parameter"""

    # This test just verifies the function signature accepts lambda_info
    # without actually running the complex function logic

    payload_dict = {
        "action": "labeled",
        "label": {"name": "wrong-label"},  # This will cause early return
        "issue": {"number": 123, "title": "Test Issue"},
        "repository": {"name": "test_repo"},
    }
    payload = cast(GitHubLabeledPayload, payload_dict)

    lambda_info: dict[str, str | None] = {
        "log_group": "/aws/lambda/pr-agent-prod",
        "log_stream": "2025/09/04/pr-agent-prod[$LATEST]841315c5",
        "request_id": "17921070-5cb6-43ee-8d2e-b5161ae89729",
    }

    # Test with lambda_info
    create_pr_from_issue(
        payload=payload,
        trigger="issue_label",
        input_from="github",
        lambda_info=lambda_info,
    )

    # Test without lambda_info (should default to None)
    create_pr_from_issue(payload=payload, trigger="issue_label", input_from="github")

    # Function calls completed without errors (early return due to wrong label)

    # create_user_request should not be called due to early return
    mock_create_user_request.assert_not_called()


def test_create_pr_from_issue_signature():
    """Test that create_pr_from_issue has the expected signature with lambda_info parameter"""

    sig = inspect.signature(create_pr_from_issue)
    params = list(sig.parameters.keys())

    # Verify lambda_info parameter exists and is optional
    assert "lambda_info" in params
    lambda_info_param = sig.parameters["lambda_info"]
    assert lambda_info_param.default is None  # Optional parameter with None default
