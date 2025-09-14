# Standard imports
from unittest.mock import patch

# Third-party imports
import pytest

# Local imports
from services.webhook.pr_body_handler import write_pr_description


@pytest.fixture
def mock_pr_payload():
    """Fixture providing a mock pull request payload."""
    return {
        "pull_request": {
            "user": {"login": "gitauto-ai[bot]"},
            "title": "GitAuto: Fix issue with authentication",
            "number": 123,
            "body": "Resolves #456\n\ngit commit -m 'Fix auth issue'",
            "url": "https://api.github.com/repos/test-owner/test-repo/pulls/123",
            "head": {"ref": "feature-branch"},
        },
        "repository": {
            "owner": {"login": "test-owner"},
            "name": "test-repo",
        },
        "installation": {"id": 12345},
    }


@pytest.fixture
def all_mocks():
    """Fixture providing all mocked dependencies."""
    with patch("services.webhook.pr_body_handler.get_installation_access_token") as mock_token, \
         patch("services.webhook.pr_body_handler.get_pull_request_file_changes") as mock_files, \
         patch("services.webhook.pr_body_handler.get_issue_body") as mock_issue, \
         patch("services.webhook.pr_body_handler.is_pull_request_open") as mock_open, \
         patch("services.webhook.pr_body_handler.check_branch_exists") as mock_branch, \
         patch("services.webhook.pr_body_handler.chat_with_ai") as mock_ai, \
         patch("services.webhook.pr_body_handler.update_pull_request_body") as mock_update:
        
        yield {
            "get_installation_access_token": mock_token,
            "get_pull_request_file_changes": mock_files,
            "get_issue_body": mock_issue,
            "is_pull_request_open": mock_open,
            "check_branch_exists": mock_branch,
            "chat_with_ai": mock_ai,
            "update_pull_request_body": mock_update,
        }


class TestWritePrDescriptionAdditional:
    """Additional test cases for write_pr_description function."""

    @patch("builtins.print")
    def test_write_pr_description_pr_closed_prints_message(
        self, mock_print, mock_pr_payload, all_mocks
    ):
        """Test that appropriate message is printed when PR is closed."""
        # Setup
        all_mocks["get_installation_access_token"].return_value = "ghs_test_token"
        all_mocks["get_pull_request_file_changes"].return_value = []
        all_mocks["get_issue_body"].return_value = "Issue description"
        all_mocks["is_pull_request_open"].return_value = False

        # Execute
        write_pr_description(mock_pr_payload)

        # Verify print message
        mock_print.assert_called_once_with("Skipping AI call: PR #123 has been closed")

    @patch("builtins.print")
    def test_write_pr_description_branch_deleted_prints_message(
        self, mock_print, mock_pr_payload, all_mocks
    ):
        """Test that appropriate message is printed when branch is deleted."""
        # Setup
        all_mocks["get_installation_access_token"].return_value = "ghs_test_token"
        all_mocks["get_pull_request_file_changes"].return_value = []
        all_mocks["get_issue_body"].return_value = "Issue description"
        all_mocks["is_pull_request_open"].return_value = True
        all_mocks["check_branch_exists"].return_value = False

        # Execute
        write_pr_description(mock_pr_payload)

        # Verify print message
        mock_print.assert_called_once_with(
            "Skipping AI call: Branch 'feature-branch' has been deleted"
        )

    def test_write_pr_description_ai_call_parameters(self, mock_pr_payload, all_mocks):
        """Test that AI call receives correct parameters."""
        # Setup
        all_mocks["get_installation_access_token"].return_value = "ghs_test_token"
        all_mocks["get_pull_request_file_changes"].return_value = [
            {"filename": "test.py", "status": "modified"}
        ]
        all_mocks["get_issue_body"].return_value = "Issue description"
        all_mocks["is_pull_request_open"].return_value = True
        all_mocks["check_branch_exists"].return_value = True
        all_mocks["chat_with_ai"].return_value = "Generated PR description"

        # Execute
        write_pr_description(mock_pr_payload)

        # Verify AI call parameters
        call_args = all_mocks["chat_with_ai"].call_args
        assert "system_input" in call_args.kwargs
        assert "user_input" in call_args.kwargs
        
        # Verify system input is the WRITE_PR_BODY prompt
        from utils.prompts.write_pr_body import WRITE_PR_BODY
        assert call_args.kwargs["system_input"] == WRITE_PR_BODY
        
        # Verify user input contains expected JSON structure
        user_input = call_args.kwargs["user_input"]
        import json
        parsed_input = json.loads(user_input)
        
        assert "owner" in parsed_input
        assert "repo" in parsed_input
        assert "issue_title" in parsed_input
        assert "issue_body" in parsed_input
        assert "file_changes" in parsed_input
        
        assert parsed_input["owner"] == "test-owner"
        assert parsed_input["repo"] == "test-repo"
        assert parsed_input["issue_title"] == "Fix issue with authentication"
        assert parsed_input["issue_body"] == "Issue description"
        assert parsed_input["file_changes"] == [{"filename": "test.py", "status": "modified"}]

    def test_write_pr_description_with_resolves_case_variations(
        self, mock_pr_payload, all_mocks
    ):
        """Test PR description generation with different case variations of 'Resolves'."""
        # Setup with lowercase 'resolves'
        mock_pr_payload["pull_request"]["body"] = "resolves #456\n\ngit commit -m 'Fix'"
        all_mocks["get_installation_access_token"].return_value = "ghs_test_token"
        all_mocks["get_pull_request_file_changes"].return_value = []
        all_mocks["is_pull_request_open"].return_value = True
        all_mocks["check_branch_exists"].return_value = True
        all_mocks["chat_with_ai"].return_value = "Generated PR description"

        # Execute
        write_pr_description(mock_pr_payload)

        # Verify issue body is not retrieved (case sensitive check)
        all_mocks["get_issue_body"].assert_not_called()

        # Verify PR body doesn't include resolves statement (case sensitive)
        expected_body = "Generated PR description\n\n```\ngit commit -m 'Fix'\n```"
        all_mocks["update_pull_request_body"].assert_called_once_with(
            url="https://api.github.com/repos/test-owner/test-repo/pulls/123",
            token="ghs_test_token",
            body=expected_body,
        )