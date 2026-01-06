# pylint: disable=too-many-lines,too-many-public-methods
"""Unit tests for pr_body_handler.py"""

from io import StringIO

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
def mock_pr_payload_non_gitauto():
    """Fixture providing a mock pull request payload from non-GitAuto user."""
    return {
        "pull_request": {
            "user": {"login": "regular-user"},
            "title": "Regular PR",
            "number": 123,
            "body": "Some changes",
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
def mock_get_installation_access_token():
    """Mock get_installation_access_token function."""
    with patch(
        "services.webhook.pr_body_handler.get_installation_access_token"
    ) as mock:
        yield mock


@pytest.fixture
def mock_get_pull_request_file_changes():
    """Mock get_pull_request_file_changes function."""
    with patch(
        "services.webhook.pr_body_handler.get_pull_request_file_changes"
    ) as mock:
        yield mock


@pytest.fixture
def mock_get_issue_body():
    """Mock get_issue_body function."""
    with patch("services.webhook.pr_body_handler.get_issue_body") as mock:
        yield mock


@pytest.fixture
def mock_is_pull_request_open():
    """Mock is_pull_request_open function."""
    with patch("services.webhook.pr_body_handler.is_pull_request_open") as mock:
        yield mock


@pytest.fixture
def mock_check_branch_exists():
    """Mock check_branch_exists function."""
    with patch("services.webhook.pr_body_handler.check_branch_exists") as mock:
        yield mock


@pytest.fixture
def mock_chat_with_ai():
    """Mock chat_with_ai function."""
    with patch("services.webhook.pr_body_handler.chat_with_ai") as mock:
        yield mock


@pytest.fixture
def mock_update_pull_request_body():
    """Mock update_pull_request_body function."""
    with patch("services.webhook.pr_body_handler.update_pull_request_body") as mock:
        yield mock


@pytest.fixture
def mock_github_app_user_name():
    """Mock GITHUB_APP_USER_NAME."""
    with patch(
        "services.webhook.pr_body_handler.GITHUB_APP_USER_NAME", "gitauto-ai[bot]"
    ) as mock:
        yield mock


@pytest.fixture
def all_mocks(
    mock_get_installation_access_token,
    mock_get_pull_request_file_changes,
    mock_get_issue_body,
    mock_is_pull_request_open,
    mock_check_branch_exists,
    mock_chat_with_ai,
    mock_update_pull_request_body,
    mock_github_app_user_name,
):
    """Fixture providing all mocked dependencies."""
    return {
        "get_installation_access_token": mock_get_installation_access_token,
        "get_pull_request_file_changes": mock_get_pull_request_file_changes,
        "get_issue_body": mock_get_issue_body,
        "is_pull_request_open": mock_is_pull_request_open,
        "check_branch_exists": mock_check_branch_exists,
        "chat_with_ai": mock_chat_with_ai,
        "update_pull_request_body": mock_update_pull_request_body,
        "github_app_user_name": mock_github_app_user_name,
    }


class TestWritePrDescription:
    """Test cases for write_pr_description function."""

    def test_write_pr_description_successful_flow(self, mock_pr_payload, all_mocks):
        """Test successful PR description generation with all components."""
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

        # Verify token retrieval
        all_mocks["get_installation_access_token"].assert_called_once_with(12345)

        # Verify file changes retrieval
        all_mocks["get_pull_request_file_changes"].assert_called_once_with(
            url="https://api.github.com/repos/test-owner/test-repo/pulls/123/files",
            token="ghs_test_token",
        )

        # Verify issue body retrieval
        all_mocks["get_issue_body"].assert_called_once_with(
            owner="test-owner",
            repo="test-repo",
            issue_number=456,
            token="ghs_test_token",
        )

        # Verify safety checks
        all_mocks["is_pull_request_open"].assert_called_once_with(
            owner="test-owner",
            repo="test-repo",
            pull_number=123,
            token="ghs_test_token",
        )
        all_mocks["check_branch_exists"].assert_called_once_with(
            owner="test-owner",
            repo="test-repo",
            branch_name="feature-branch",
            token="ghs_test_token",
        )

        # Verify AI call
        all_mocks["chat_with_ai"].assert_called_once()
        call_args = all_mocks["chat_with_ai"].call_args
        assert "system_input" in call_args.kwargs
        assert "user_input" in call_args.kwargs

        # Verify PR body update
        expected_body = (
            "Resolves #456\n\n"
            "Generated PR description\n\n"
            "```\n"
            "git commit -m 'Fix auth issue'\n"
            "```"
        )
        all_mocks["update_pull_request_body"].assert_called_once_with(
            url="https://api.github.com/repos/test-owner/test-repo/pulls/123",
            token="ghs_test_token",
            body=expected_body,
        )

    def test_write_pr_description_non_gitauto_user_returns_early(
        self, mock_pr_payload_non_gitauto, all_mocks
    ):
        """Test that function returns early for non-GitAuto users."""
        # Execute
        write_pr_description(mock_pr_payload_non_gitauto)

        # Verify no functions are called
        all_mocks["get_installation_access_token"].assert_not_called()
        all_mocks["get_pull_request_file_changes"].assert_not_called()
        all_mocks["get_issue_body"].assert_not_called()
        all_mocks["is_pull_request_open"].assert_not_called()
        all_mocks["check_branch_exists"].assert_not_called()
        all_mocks["chat_with_ai"].assert_not_called()
        all_mocks["update_pull_request_body"].assert_not_called()

    def test_write_pr_description_without_gitauto_prefix(
        self, mock_pr_payload, all_mocks
    ):
        """Test PR title processing without GitAuto prefix."""
        # Setup
        mock_pr_payload["pull_request"]["title"] = "Fix issue with authentication"
        all_mocks["get_installation_access_token"].return_value = "ghs_test_token"
        all_mocks["get_pull_request_file_changes"].return_value = []
        all_mocks["get_issue_body"].return_value = "Issue description"
        all_mocks["is_pull_request_open"].return_value = True
        all_mocks["check_branch_exists"].return_value = True
        all_mocks["chat_with_ai"].return_value = "Generated PR description"

        # Execute
        write_pr_description(mock_pr_payload)

        # Verify AI call with correct title
        call_args = all_mocks["chat_with_ai"].call_args
        user_input = call_args.kwargs["user_input"]
        assert '"issue_title": "Fix issue with authentication"' in user_input

    def test_write_pr_description_without_resolves_statement(
        self, mock_pr_payload, all_mocks
    ):
        """Test PR description generation without resolves statement."""
        # Setup
        mock_pr_payload["pull_request"]["body"] = "Some PR body without resolves"
        all_mocks["get_installation_access_token"].return_value = "ghs_test_token"
        all_mocks["get_pull_request_file_changes"].return_value = []
        all_mocks["is_pull_request_open"].return_value = True
        all_mocks["check_branch_exists"].return_value = True
        all_mocks["chat_with_ai"].return_value = "Generated PR description"

        # Execute
        write_pr_description(mock_pr_payload)

        # Verify issue body is not retrieved
        all_mocks["get_issue_body"].assert_not_called()

        # Verify PR body update without resolves statement
        expected_body = "Generated PR description\n\n```\n\n```"
        all_mocks["update_pull_request_body"].assert_called_once_with(
            url="https://api.github.com/repos/test-owner/test-repo/pulls/123",
            token="ghs_test_token",
            body=expected_body,
        )

    def test_write_pr_description_with_multiple_git_commands(
        self, mock_pr_payload, all_mocks
    ):
        """Test PR description generation with multiple git commands."""
        # Setup
        mock_pr_payload["pull_request"]["body"] = (
            "Resolves #456\n\n"
            "git add .\n"
            "git commit -m 'Fix auth issue'\n"
            "git push origin feature-branch"
        )
        all_mocks["get_installation_access_token"].return_value = "ghs_test_token"
        all_mocks["get_pull_request_file_changes"].return_value = []
        all_mocks["get_issue_body"].return_value = "Issue description"
        all_mocks["is_pull_request_open"].return_value = True
        all_mocks["check_branch_exists"].return_value = True
        all_mocks["chat_with_ai"].return_value = "Generated PR description"

        # Execute
        write_pr_description(mock_pr_payload)

        # Verify PR body update with multiple commands
        expected_body = (
            "Resolves #456\n\n"
            "Generated PR description\n\n"
            "```\n"
            "git add .\n"
            "git commit -m 'Fix auth issue'\n"
            "git push origin feature-branch\n"
            "```"
        )
        all_mocks["update_pull_request_body"].assert_called_once_with(
            url="https://api.github.com/repos/test-owner/test-repo/pulls/123",
            token="ghs_test_token",
            body=expected_body,
        )

    def test_write_pr_description_pr_closed_skips_ai_call(
        self, mock_pr_payload, all_mocks
    ):
        """Test that AI call is skipped when PR is closed."""
        # Setup
        all_mocks["get_installation_access_token"].return_value = "ghs_test_token"
        all_mocks["get_pull_request_file_changes"].return_value = []
        all_mocks["get_issue_body"].return_value = "Issue description"
        all_mocks["is_pull_request_open"].return_value = False
        all_mocks["check_branch_exists"].return_value = True

        # Execute
        write_pr_description(mock_pr_payload)

        # Verify AI call and PR update are skipped
        all_mocks["chat_with_ai"].assert_not_called()
        all_mocks["update_pull_request_body"].assert_not_called()

    def test_write_pr_description_branch_deleted_skips_ai_call(
        self, mock_pr_payload, all_mocks
    ):
        """Test that AI call is skipped when branch is deleted."""
        # Setup
        all_mocks["get_installation_access_token"].return_value = "ghs_test_token"
        all_mocks["get_pull_request_file_changes"].return_value = []
        all_mocks["get_issue_body"].return_value = "Issue description"
        all_mocks["is_pull_request_open"].return_value = True
        all_mocks["check_branch_exists"].return_value = False

        # Execute
        write_pr_description(mock_pr_payload)

        # Verify AI call and PR update are skipped
        all_mocks["chat_with_ai"].assert_not_called()
        all_mocks["update_pull_request_body"].assert_not_called()

    def test_write_pr_description_with_none_issue_body(
        self, mock_pr_payload, all_mocks
    ):
        """Test PR description generation when issue body is None."""
        # Setup
        all_mocks["get_installation_access_token"].return_value = "ghs_test_token"
        all_mocks["get_pull_request_file_changes"].return_value = []
        all_mocks["get_issue_body"].return_value = None
        all_mocks["is_pull_request_open"].return_value = True
        all_mocks["check_branch_exists"].return_value = True
        all_mocks["chat_with_ai"].return_value = "Generated PR description"

        # Execute
        write_pr_description(mock_pr_payload)

        # Verify AI call with empty issue body
        call_args = all_mocks["chat_with_ai"].call_args
        user_input = call_args.kwargs["user_input"]
        assert '"issue_body": ""' in user_input

    def test_write_pr_description_with_empty_file_changes(
        self, mock_pr_payload, all_mocks
    ):
        """Test PR description generation with empty file changes."""
        # Setup
        all_mocks["get_installation_access_token"].return_value = "ghs_test_token"
        all_mocks["get_pull_request_file_changes"].return_value = []
        all_mocks["get_issue_body"].return_value = "Issue description"
        all_mocks["is_pull_request_open"].return_value = True
        all_mocks["check_branch_exists"].return_value = True
        all_mocks["chat_with_ai"].return_value = "Generated PR description"

        # Execute
        write_pr_description(mock_pr_payload)

        # Verify AI call with empty file changes
        call_args = all_mocks["chat_with_ai"].call_args
        user_input = call_args.kwargs["user_input"]
        assert '"file_changes": []' in user_input

    def test_write_pr_description_with_complex_file_changes(
        self, mock_pr_payload, all_mocks
    ):
        """Test PR description generation with complex file changes."""
        # Setup
        file_changes = [
            {"filename": "src/main.py", "status": "modified", "additions": 10},
            {"filename": "tests/test_main.py", "status": "added", "additions": 50},
            {"filename": "old_file.py", "status": "removed", "deletions": 20},
        ]
        all_mocks["get_installation_access_token"].return_value = "ghs_test_token"
        all_mocks["get_pull_request_file_changes"].return_value = file_changes
        all_mocks["get_issue_body"].return_value = "Issue description"
        all_mocks["is_pull_request_open"].return_value = True
        all_mocks["check_branch_exists"].return_value = True
        all_mocks["chat_with_ai"].return_value = "Generated PR description"

        # Execute
        write_pr_description(mock_pr_payload)

        # Verify AI call with complex file changes
        call_args = all_mocks["chat_with_ai"].call_args
        user_input = call_args.kwargs["user_input"]
        assert '"file_changes":' in user_input
        assert "src/main.py" in user_input
        assert "tests/test_main.py" in user_input
        assert "old_file.py" in user_input

    def test_write_pr_description_with_multiline_pr_body(
        self, mock_pr_payload, all_mocks
    ):
        """Test PR description generation with multiline PR body."""
        # Setup
        mock_pr_payload["pull_request"]["body"] = (
            "Resolves #456\n"
            "This is a description\n"
            "git add .\n"
            "Some other line\n"
            "git commit -m 'Fix auth issue'\n"
            "Final line"
        )
        all_mocks["get_installation_access_token"].return_value = "ghs_test_token"
        all_mocks["get_pull_request_file_changes"].return_value = []
        all_mocks["get_issue_body"].return_value = "Issue description"
        all_mocks["is_pull_request_open"].return_value = True
        all_mocks["check_branch_exists"].return_value = True
        all_mocks["chat_with_ai"].return_value = "Generated PR description"

        # Execute
        write_pr_description(mock_pr_payload)

        # Verify PR body update with extracted commands
        expected_body = (
            "Resolves #456\n\n"
            "Generated PR description\n\n"
            "```\n"
            "git add .\n"
            "git commit -m 'Fix auth issue'\n"
            "```"
        )
        all_mocks["update_pull_request_body"].assert_called_once_with(
            url="https://api.github.com/repos/test-owner/test-repo/pulls/123",
            token="ghs_test_token",
            body=expected_body,
        )

    def test_write_pr_description_with_invalid_issue_number(
        self, mock_pr_payload, all_mocks
    ):
        """Test PR description generation with invalid issue number format."""
        # Setup
        mock_pr_payload["pull_request"]["body"] = "Resolves #invalid"
        all_mocks["get_installation_access_token"].return_value = "ghs_test_token"
        all_mocks["get_pull_request_file_changes"].return_value = []
        all_mocks["is_pull_request_open"].return_value = True
        all_mocks["check_branch_exists"].return_value = True
        all_mocks["chat_with_ai"].return_value = "Generated PR description"

        # Execute - should handle ValueError gracefully
        write_pr_description(mock_pr_payload)

        # Verify issue body is not retrieved due to invalid number
        all_mocks["get_issue_body"].assert_not_called()

    def test_write_pr_description_with_multiple_resolves_statements(
        self, mock_pr_payload, all_mocks
    ):
        """Test PR description generation with multiple resolves statements."""
        # Setup
        mock_pr_payload["pull_request"]["body"] = (
            "Resolves #456\n"
            "Some description\n"
            "Resolves #789\n"
            "git commit -m 'Fix issues'"
        )
        all_mocks["get_installation_access_token"].return_value = "ghs_test_token"
        all_mocks["get_pull_request_file_changes"].return_value = []
        all_mocks["get_issue_body"].return_value = "Issue description"
        all_mocks["is_pull_request_open"].return_value = True
        all_mocks["check_branch_exists"].return_value = True
        all_mocks["chat_with_ai"].return_value = "Generated PR description"

        # Execute
        write_pr_description(mock_pr_payload)

        # Verify only first issue is processed
        all_mocks["get_issue_body"].assert_called_once_with(
            owner="test-owner",
            repo="test-repo",
            issue_number=456,
            token="ghs_test_token",
        )

        # Verify only first resolves statement is used
        expected_body = (
            "Resolves #456\n\n"
            "Generated PR description\n\n"
            "```\n"
            "git commit -m 'Fix issues'\n"
            "```"
        )
        all_mocks["update_pull_request_body"].assert_called_once_with(
            url="https://api.github.com/repos/test-owner/test-repo/pulls/123",
            token="ghs_test_token",
            body=expected_body,
        )

    def test_write_pr_description_with_empty_pr_body(self, mock_pr_payload, all_mocks):
        """Test PR description generation with empty PR body."""
        # Setup
        mock_pr_payload["pull_request"]["body"] = ""
        all_mocks["get_installation_access_token"].return_value = "ghs_test_token"
        all_mocks["get_pull_request_file_changes"].return_value = []
        all_mocks["is_pull_request_open"].return_value = True
        all_mocks["check_branch_exists"].return_value = True
        all_mocks["chat_with_ai"].return_value = "Generated PR description"

        # Execute
        write_pr_description(mock_pr_payload)

        # Verify no issue body retrieval
        all_mocks["get_issue_body"].assert_not_called()

        # Verify PR body update without resolves statement or commands
        expected_body = "Generated PR description\n\n```\n\n```"
        all_mocks["update_pull_request_body"].assert_called_once_with(
            url="https://api.github.com/repos/test-owner/test-repo/pulls/123",
            token="ghs_test_token",
            body=expected_body,
        )

    def test_write_pr_description_with_none_pr_body(self, mock_pr_payload, all_mocks):
        """Test PR description generation with None PR body."""
        # Setup
        mock_pr_payload["pull_request"]["body"] = None
        all_mocks["get_installation_access_token"].return_value = "ghs_test_token"
        all_mocks["get_pull_request_file_changes"].return_value = []
        all_mocks["is_pull_request_open"].return_value = True
        all_mocks["check_branch_exists"].return_value = True
        all_mocks["chat_with_ai"].return_value = "Generated PR description"

        # Execute - should handle None gracefully
        write_pr_description(mock_pr_payload)

        # Verify no issue body retrieval
        all_mocks["get_issue_body"].assert_not_called()

    def test_write_pr_description_with_string_pull_number(
        self, mock_pr_payload, all_mocks
    ):
        """Test PR description generation with string pull number."""
        # Setup
        mock_pr_payload["pull_request"]["number"] = "123"
        all_mocks["get_installation_access_token"].return_value = "ghs_test_token"
        all_mocks["get_pull_request_file_changes"].return_value = []
        all_mocks["get_issue_body"].return_value = "Issue description"
        all_mocks["is_pull_request_open"].return_value = True
        all_mocks["check_branch_exists"].return_value = True
        all_mocks["chat_with_ai"].return_value = "Generated PR description"

        # Execute
        write_pr_description(mock_pr_payload)

        # Verify safety checks with string number
        all_mocks["is_pull_request_open"].assert_called_once_with(
            owner="test-owner",
            repo="test-repo",
            pull_number="123",
            token="ghs_test_token",
        )

    def test_write_pr_description_with_string_installation_id(
        self, mock_pr_payload, all_mocks
    ):
        """Test PR description generation with string installation ID."""
        # Setup
        mock_pr_payload["installation"]["id"] = "12345"
        all_mocks["get_installation_access_token"].return_value = "ghs_test_token"
        all_mocks["get_pull_request_file_changes"].return_value = []
        all_mocks["get_issue_body"].return_value = "Issue description"
        all_mocks["is_pull_request_open"].return_value = True
        all_mocks["check_branch_exists"].return_value = True
        all_mocks["chat_with_ai"].return_value = "Generated PR description"

        # Execute
        write_pr_description(mock_pr_payload)

        # Verify token retrieval with string ID
        all_mocks["get_installation_access_token"].assert_called_once_with("12345")

    def test_write_pr_description_with_unicode_characters(
        self, mock_pr_payload, all_mocks
    ):
        """Test PR description generation with unicode characters."""
        # Setup
        mock_pr_payload["pull_request"][
            "title"
        ] = "GitAuto: Fïx ïssüé wïth äüthéntïcätïön"
        mock_pr_payload["repository"]["owner"]["login"] = "tëst-öwnér"
        mock_pr_payload["repository"]["name"] = "tëst-rëpö"
        all_mocks["get_installation_access_token"].return_value = "ghs_test_token"
        all_mocks["get_pull_request_file_changes"].return_value = []
        all_mocks["get_issue_body"].return_value = "Ïssüé dëscrïptïön"
        all_mocks["is_pull_request_open"].return_value = True
        all_mocks["check_branch_exists"].return_value = True
        all_mocks["chat_with_ai"].return_value = "Gënërätëd PR dëscrïptïön"

        # Execute
        write_pr_description(mock_pr_payload)

        # Verify calls with unicode characters
        all_mocks["get_issue_body"].assert_called_once_with(
            owner="tëst-öwnér",
            repo="tëst-rëpö",
            issue_number=456,
            token="ghs_test_token",
        )

        # Verify AI call with unicode title
        call_args = all_mocks["chat_with_ai"].call_args
        user_input = call_args.kwargs["user_input"]
        # Unicode characters are escaped in JSON, so check for escaped sequences
        assert (
            "F\\u00efx \\u00efss\\u00fc\\u00e9 w\\u00efth \\u00e4\\u00fcth\\u00e9nt\\u00efc\\u00e4t\\u00ef\\u00f6n"
            in user_input
        )

    def test_write_pr_description_with_special_characters_in_branch(
        self, mock_pr_payload, all_mocks
    ):
        """Test PR description generation with special characters in branch name."""
        # Setup
        mock_pr_payload["pull_request"]["head"]["ref"] = "feature/fix-issue#456"
        all_mocks["get_installation_access_token"].return_value = "ghs_test_token"
        all_mocks["get_pull_request_file_changes"].return_value = []
        all_mocks["get_issue_body"].return_value = "Issue description"
        all_mocks["is_pull_request_open"].return_value = True
        all_mocks["check_branch_exists"].return_value = True
        all_mocks["chat_with_ai"].return_value = "Generated PR description"

        # Execute
        write_pr_description(mock_pr_payload)

        # Verify branch check with special characters
        all_mocks["check_branch_exists"].assert_called_once_with(
            owner="test-owner",
            repo="test-repo",
            branch_name="feature/fix-issue#456",
            token="ghs_test_token",
        )

    def test_write_pr_description_with_very_long_title(
        self, mock_pr_payload, all_mocks
    ):
        """Test PR description generation with very long title."""
        # Setup
        long_title = "GitAuto: " + "a" * 1000
        mock_pr_payload["pull_request"]["title"] = long_title
        all_mocks["get_installation_access_token"].return_value = "ghs_test_token"
        all_mocks["get_pull_request_file_changes"].return_value = []
        all_mocks["get_issue_body"].return_value = "Issue description"
        all_mocks["is_pull_request_open"].return_value = True
        all_mocks["check_branch_exists"].return_value = True
        all_mocks["chat_with_ai"].return_value = "Generated PR description"

        # Execute
        write_pr_description(mock_pr_payload)

        # Verify AI call with long title (without GitAuto prefix)
        call_args = all_mocks["chat_with_ai"].call_args
        user_input = call_args.kwargs["user_input"]
        assert '"issue_title": "' + "a" * 1000 + '"' in user_input

    def test_write_pr_description_with_zero_issue_number(
        self, mock_pr_payload, all_mocks
    ):
        """Test PR description generation with zero issue number."""
        # Setup
        mock_pr_payload["pull_request"]["body"] = "Resolves #0\n\ngit commit -m 'Fix'"
        all_mocks["get_installation_access_token"].return_value = "ghs_test_token"
        all_mocks["get_pull_request_file_changes"].return_value = []
        all_mocks["get_issue_body"].return_value = "Issue description"
        all_mocks["is_pull_request_open"].return_value = True
        all_mocks["check_branch_exists"].return_value = True
        all_mocks["chat_with_ai"].return_value = "Generated PR description"

        # Execute
        write_pr_description(mock_pr_payload)

        # Verify issue body retrieval with zero issue number
        all_mocks["get_issue_body"].assert_called_once_with(
            owner="test-owner",
            repo="test-repo",
            issue_number=0,
            token="ghs_test_token",
        )

    def test_write_pr_description_with_negative_issue_number(
        self, mock_pr_payload, all_mocks
    ):
        """Test PR description generation with negative issue number."""
        # Setup
        mock_pr_payload["pull_request"]["body"] = "Resolves #-1\n\ngit commit -m 'Fix'"
        all_mocks["get_installation_access_token"].return_value = "ghs_test_token"
        all_mocks["get_pull_request_file_changes"].return_value = []
        all_mocks["get_issue_body"].return_value = "Issue description"
        all_mocks["is_pull_request_open"].return_value = True
        all_mocks["check_branch_exists"].return_value = True
        all_mocks["chat_with_ai"].return_value = "Generated PR description"

        # Execute
        write_pr_description(mock_pr_payload)

        # Verify issue body retrieval with negative issue number
        all_mocks["get_issue_body"].assert_called_once_with(
            owner="test-owner",
            repo="test-repo",
            issue_number=-1,
            token="ghs_test_token",
        )

    def test_write_pr_description_with_large_issue_number(
        self, mock_pr_payload, all_mocks
    ):
        """Test PR description generation with large issue number."""
        # Setup
        large_number = 999999999
        mock_pr_payload["pull_request"][
            "body"
        ] = f"Resolves #{large_number}\n\ngit commit -m 'Fix'"
        all_mocks["get_installation_access_token"].return_value = "ghs_test_token"
        all_mocks["get_pull_request_file_changes"].return_value = []
        all_mocks["get_issue_body"].return_value = "Issue description"
        all_mocks["is_pull_request_open"].return_value = True
        all_mocks["check_branch_exists"].return_value = True
        all_mocks["chat_with_ai"].return_value = "Generated PR description"

        # Execute
        write_pr_description(mock_pr_payload)

        # Verify issue body retrieval with large issue number
        all_mocks["get_issue_body"].assert_called_once_with(
            owner="test-owner",
            repo="test-repo",
            issue_number=large_number,
            token="ghs_test_token",
        )

    def test_write_pr_description_with_git_commands_containing_quotes(
        self, mock_pr_payload, all_mocks
    ):
        """Test PR description generation with git commands containing quotes."""
        # Setup
        mock_pr_payload["pull_request"]["body"] = (
            "Resolves #456\n\n"
            'git commit -m "Fix issue with \\"quotes\\""\n'
            "git commit -m 'Fix issue with \"double quotes\"'"
        )
        all_mocks["get_installation_access_token"].return_value = "ghs_test_token"
        all_mocks["get_pull_request_file_changes"].return_value = []
        all_mocks["get_issue_body"].return_value = "Issue description"
        all_mocks["is_pull_request_open"].return_value = True
        all_mocks["check_branch_exists"].return_value = True
        all_mocks["chat_with_ai"].return_value = "Generated PR description"

        # Execute
        write_pr_description(mock_pr_payload)

        # Verify PR body update with quoted commands
        expected_body = (
            "Resolves #456\n\n"
            "Generated PR description\n\n"
            "```\n"
            'git commit -m "Fix issue with \\"quotes\\""\n'
            "git commit -m 'Fix issue with \"double quotes\"'\n"
            "```"
        )
        all_mocks["update_pull_request_body"].assert_called_once_with(
            url="https://api.github.com/repos/test-owner/test-repo/pulls/123",
            token="ghs_test_token",
            body=expected_body,
        )

    def test_write_pr_description_with_empty_git_commands(
        self, mock_pr_payload, all_mocks
    ):
        """Test PR description generation with git commands that have minimal content."""
        # Setup
        mock_pr_payload["pull_request"]["body"] = (
            "Resolves #456\n\n"
            "git \n"  # This will be included (starts with 'git ')
            "git"  # This will be skipped (doesn't start with 'git ')
        )
        all_mocks["get_installation_access_token"].return_value = "ghs_test_token"
        all_mocks["get_pull_request_file_changes"].return_value = []
        all_mocks["get_issue_body"].return_value = "Issue description"
        all_mocks["is_pull_request_open"].return_value = True
        all_mocks["check_branch_exists"].return_value = True
        all_mocks["chat_with_ai"].return_value = "Generated PR description"

        # Execute
        write_pr_description(mock_pr_payload)

        # Verify PR body update with minimal git commands (only 'git ' is included)
        expected_body = "Resolves #456\n\nGenerated PR description\n\n```\ngit \n```"
        all_mocks["update_pull_request_body"].assert_called_once_with(
            url="https://api.github.com/repos/test-owner/test-repo/pulls/123",
            token="ghs_test_token",
            body=expected_body,
        )

    def test_write_pr_description_with_mixed_case_gitauto_user(
        self, mock_pr_payload, all_mocks
    ):
        """Test PR description generation with mixed case GitAuto user."""
        # Setup
        mock_pr_payload["pull_request"]["user"]["login"] = "GitAuto-AI[bot]"
        all_mocks["get_installation_access_token"].return_value = "ghs_test_token"
        all_mocks["get_pull_request_file_changes"].return_value = []
        all_mocks["get_issue_body"].return_value = "Issue description"
        all_mocks["is_pull_request_open"].return_value = True
        all_mocks["check_branch_exists"].return_value = True
        all_mocks["chat_with_ai"].return_value = "Generated PR description"

        # Execute - should return early due to case sensitivity
        write_pr_description(mock_pr_payload)

        # Verify no functions are called due to case mismatch
        all_mocks["get_installation_access_token"].assert_not_called()

    def test_write_pr_description_with_whitespace_in_user_login(
        self, mock_pr_payload, all_mocks
    ):
        """Test PR description generation with whitespace in user login."""
        # Setup
        mock_pr_payload["pull_request"]["user"]["login"] = " gitauto-ai[bot] "
        all_mocks["get_installation_access_token"].return_value = "ghs_test_token"

        # Execute - should return early due to whitespace
        write_pr_description(mock_pr_payload)

        # Verify no functions are called due to whitespace
        all_mocks["get_installation_access_token"].assert_not_called()

    def test_write_pr_description_with_missing_payload_fields(self, all_mocks):
        """Test PR description generation with missing payload fields."""
        # Setup incomplete payload
        incomplete_payload = {
            "pull_request": {
                "user": {"login": "gitauto-ai[bot]"},
                "title": "GitAuto: Fix issue",
            },
            "repository": {
                "owner": {"login": "test-owner"},
            },
        }

        # Execute - should handle missing fields gracefully
        write_pr_description(incomplete_payload)

        # Verify no functions are called due to missing fields
        all_mocks["get_installation_access_token"].assert_not_called()

    def test_write_pr_description_with_none_payload(self, all_mocks):
        """Test PR description generation with None payload."""
        # Execute - should handle empty dict gracefully
        write_pr_description({})

        # Verify no functions are called
        all_mocks["get_installation_access_token"].assert_not_called()

    def test_write_pr_description_with_empty_payload(self, all_mocks):
        """Test PR description generation with empty payload."""
        # Execute - should handle empty payload gracefully
        write_pr_description({})

        # Verify no functions are called
        all_mocks["get_installation_access_token"].assert_not_called()

    @patch("services.webhook.pr_body_handler.GITHUB_APP_USER_NAME", "custom-bot")
    def test_write_pr_description_with_custom_github_app_user_name(
        self, mock_pr_payload, all_mocks
    ):
        """Test PR description generation with custom GitHub app user name."""
        # Setup
        mock_pr_payload["pull_request"]["user"]["login"] = "custom-bot"
        all_mocks["get_installation_access_token"].return_value = "ghs_test_token"
        all_mocks["get_pull_request_file_changes"].return_value = []
        all_mocks["get_issue_body"].return_value = "Issue description"
        all_mocks["is_pull_request_open"].return_value = True
        all_mocks["check_branch_exists"].return_value = True
        all_mocks["chat_with_ai"].return_value = "Generated PR description"

        # Execute
        write_pr_description(mock_pr_payload)

        # Verify function proceeds with custom user name
        all_mocks["get_installation_access_token"].assert_called_once_with(12345)

    def test_write_pr_description_with_json_serialization_edge_cases(
        self, mock_pr_payload, all_mocks
    ):
        """Test PR description generation with JSON serialization edge cases."""
        # Setup with special characters that might affect JSON
        mock_pr_payload["repository"]["owner"]["login"] = 'test"owner'
        mock_pr_payload["repository"]["name"] = "test\\repo"
        file_changes = [{"filename": "file\nwith\nnewlines.py", "status": "modified"}]
        all_mocks["get_installation_access_token"].return_value = "ghs_test_token"
        all_mocks["get_pull_request_file_changes"].return_value = file_changes
        all_mocks["get_issue_body"].return_value = 'Issue with "quotes" and \n newlines'
        all_mocks["is_pull_request_open"].return_value = True
        all_mocks["check_branch_exists"].return_value = True
        all_mocks["chat_with_ai"].return_value = "Generated PR description"

        # Execute - should handle JSON serialization properly
        write_pr_description(mock_pr_payload)

        # Verify AI call was made (JSON serialization succeeded)
        all_mocks["chat_with_ai"].assert_called_once()
        call_args = all_mocks["chat_with_ai"].call_args
        user_input = call_args.kwargs["user_input"]

        # Verify JSON is properly escaped
        assert 'test"owner' in user_input or 'test\\"owner' in user_input
        assert "test\\repo" in user_input or "test\\\\repo" in user_input

    def test_write_pr_description_with_none_payload_explicit(self, all_mocks):
        """Test PR description generation with explicit None payload."""
        # Execute - should handle None payload gracefully
        write_pr_description(None)

        # Verify no functions are called
        all_mocks["get_installation_access_token"].assert_not_called()
        all_mocks["get_pull_request_file_changes"].assert_not_called()
        all_mocks["get_issue_body"].assert_not_called()
        all_mocks["is_pull_request_open"].assert_not_called()
        all_mocks["check_branch_exists"].assert_not_called()

    def test_write_pr_description_token_retrieval_failure(
        self, mock_pr_payload, all_mocks
    ):
        """Test PR description generation when token retrieval fails."""
        # Setup - get_installation_access_token now raises instead of returning None
        all_mocks["get_installation_access_token"].side_effect = ValueError(
            "Installation 12345 suspended or deleted"
        )

        # Execute - exception propagates since no handle_exceptions decorator
        with pytest.raises(ValueError, match="Installation 12345 suspended or deleted"):
            write_pr_description(mock_pr_payload)

        # Verify token retrieval was attempted
        all_mocks["get_installation_access_token"].assert_called_once_with(12345)

        # Verify no further functions are called after token failure
        all_mocks["get_pull_request_file_changes"].assert_not_called()
        all_mocks["get_issue_body"].assert_not_called()
        all_mocks["is_pull_request_open"].assert_not_called()

    @patch("sys.stdout", new_callable=StringIO)
    def test_write_pr_description_pr_closed_prints_message(
        self, mock_stdout, mock_pr_payload, all_mocks
    ):
        """Test that closing PR prints appropriate message."""
        # Setup
        all_mocks["get_installation_access_token"].return_value = "ghs_test_token"
        all_mocks["get_pull_request_file_changes"].return_value = []
        all_mocks["get_issue_body"].return_value = "Issue description"
        all_mocks["is_pull_request_open"].return_value = False
        all_mocks["check_branch_exists"].return_value = True

        # Execute
        write_pr_description(mock_pr_payload)

        # Verify print message
        output = mock_stdout.getvalue()
        assert "Skipping AI call: PR #123 has been closed" in output

    @patch("sys.stdout", new_callable=StringIO)
    def test_write_pr_description_branch_deleted_prints_message(
        self, mock_stdout, mock_pr_payload, all_mocks
    ):
        """Test that deleted branch prints appropriate message."""
        # Setup
        all_mocks["get_installation_access_token"].return_value = "ghs_test_token"
        all_mocks["get_pull_request_file_changes"].return_value = []
        all_mocks["get_issue_body"].return_value = "Issue description"
        all_mocks["is_pull_request_open"].return_value = True
        all_mocks["check_branch_exists"].return_value = False

        # Execute
        write_pr_description(mock_pr_payload)

        # Verify print message
        output = mock_stdout.getvalue()
        assert "Skipping AI call: Branch 'feature-branch' has been deleted" in output

    def test_write_pr_description_with_malformed_resolves_statement(
        self, mock_pr_payload, all_mocks
    ):
        """Test PR description generation with malformed resolves statement."""
        # Setup with malformed resolves statement (no issue number after #)
        mock_pr_payload["pull_request"]["body"] = "Resolves #\n\ngit commit -m 'Fix'"
        all_mocks["get_installation_access_token"].return_value = "ghs_test_token"
        all_mocks["get_pull_request_file_changes"].return_value = []
        all_mocks["is_pull_request_open"].return_value = True
        all_mocks["check_branch_exists"].return_value = True
        all_mocks["chat_with_ai"].return_value = "Generated PR description"

        # Execute - should handle IndexError gracefully
        write_pr_description(mock_pr_payload)

        # Verify issue body is not retrieved due to malformed resolves statement
        all_mocks["get_issue_body"].assert_not_called()

        # Verify AI call still proceeds
        all_mocks["chat_with_ai"].assert_called_once()
        all_mocks["update_pull_request_body"].assert_called_once()

    # pylint: disable=redefined-outer-name
    # This is needed because pytest fixtures can have the same name as test parameters
