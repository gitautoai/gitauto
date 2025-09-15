from unittest.mock import patch, MagicMock
from datetime import datetime
from typing import cast
import pytest
from schemas.supabase.types import Coverages, Repositories
from services.github.types.pull_request_webhook_payload import PullRequestWebhookPayload
from services.github.pulls.get_pull_request_files import FileChange
from services.webhook.utils.create_pr_checkbox_comment import create_pr_checkbox_comment


def create_mock_payload(
    sender_login: str = "testuser",
    repo_id: int = 123,
    repo_name: str = "test-repo",
    owner_id: int = 456,
    owner_login: str = "testowner",
    pull_number: int = 1,
    pull_url: str = "https://api.github.com/repos/testowner/test-repo/pulls/1",
    installation_id: int = 789,
    branch_name: str = "feature-branch",
) -> PullRequestWebhookPayload:
    """Helper function to create a mock webhook payload."""
    return cast(
        PullRequestWebhookPayload,
        {
            "action": "opened",
            "number": pull_number,
            "pull_request": {
                "number": pull_number,
                "url": pull_url,
                "head": {"ref": branch_name},
            },
            "repository": {
                "id": repo_id,
                "name": repo_name,
                "owner": {"id": owner_id, "login": owner_login},
            },
            "organization": {"id": owner_id, "login": owner_login},
            "sender": {"login": sender_login},
            "installation": {"id": installation_id},
        },
    )


def create_mock_repository(
    repo_id: int = 123, trigger_on_pr_change: bool = True
) -> Repositories:
    """Helper function to create a mock repository."""
    return cast(
        Repositories,
        {
            "id": 1,
            "owner_id": 456,
            "repo_id": repo_id,
            "repo_name": "test-repo",
            "created_at": datetime.now(),
            "created_by": "testuser",
            "updated_at": datetime.now(),
            "updated_by": "testuser",
            "use_screenshots": False,
            "production_url": None,
            "local_port": None,
            "startup_commands": None,
            "web_urls": None,
            "file_paths": None,
            "repo_rules": None,
            "file_count": 100,
            "blank_lines": 10,
            "comment_lines": 20,
            "code_lines": 70,
            "target_branch": "main",
            "trigger_on_review_comment": True,
            "trigger_on_test_failure": True,
            "trigger_on_commit": True,
            "trigger_on_merged": True,
            "trigger_on_schedule": False,
            "schedule_frequency": None,
            "schedule_minute": None,
            "schedule_time": None,
            "schedule_day_of_week": None,
            "schedule_include_weekends": False,
            "structured_rules": None,
            "trigger_on_pr_change": trigger_on_pr_change,
            "schedule_execution_count": 0,
            "schedule_interval_minutes": 60,
        },
    )


def create_file_change(filename: str, status: str = "modified") -> FileChange:
    """Helper function to create a FileChange object."""
    return {"filename": filename, "status": status}


def create_coverage_data(
    filename: str,
    line_coverage: float | None = None,
    function_coverage: float | None = None,
    branch_coverage: float | None = None,
    **overrides,
) -> Coverages:
    """Helper function to create coverage data."""
    base_data = {
        "id": 1,
        "owner_id": 456,
        "repo_id": 123,
        "language": "python",
        "package_name": "test_package",
        "level": "file",
        "full_path": filename,
        "statement_coverage": 80.0,
        "function_coverage": function_coverage,
        "branch_coverage": branch_coverage,
        "path_coverage": 60.0,
        "line_coverage": line_coverage,
        "uncovered_lines": "1,2,3",
        "created_at": datetime.now(),
        "created_by": "testuser",
        "updated_at": datetime.now(),
        "updated_by": "testuser",
        "github_issue_url": None,
        "uncovered_functions": "func1,func2",
        "uncovered_branches": "branch1,branch2",
        "branch_name": "main",
        "file_size": 1000,
        "is_excluded_from_testing": False,
    }
    base_data.update(overrides)
    return cast(Coverages, base_data)


@pytest.fixture
def mock_get_repository():
    """Mock the get_repository function."""
    with patch(
        "services.webhook.utils.create_pr_checkbox_comment.get_repository"
    ) as mock:
        yield mock


@pytest.fixture
def mock_get_installation_access_token():
    """Mock the get_installation_access_token function."""
    with patch(
        "services.webhook.utils.create_pr_checkbox_comment.get_installation_access_token"
    ) as mock:
        mock.return_value = "mock_token"
        yield mock


@pytest.fixture
def mock_get_pull_request_files():
    """Mock the get_pull_request_files function."""
    with patch(
        "services.webhook.utils.create_pr_checkbox_comment.get_pull_request_files"
    ) as mock:
        yield mock


@pytest.fixture
def mock_is_code_file():
    """Mock the is_code_file function."""
    with patch("services.webhook.utils.create_pr_checkbox_comment.is_code_file") as mock:
        yield mock


@pytest.fixture
def mock_is_test_file():
    """Mock the is_test_file function."""
    with patch("services.webhook.utils.create_pr_checkbox_comment.is_test_file") as mock:
        yield mock


@pytest.fixture
def mock_is_type_file():
    """Mock the is_type_file function."""
    with patch("services.webhook.utils.create_pr_checkbox_comment.is_type_file") as mock:
        yield mock


@pytest.fixture
def mock_get_coverages():
    """Mock the get_coverages function."""
    with patch(
        "services.webhook.utils.create_pr_checkbox_comment.get_coverages"
    ) as mock:
        yield mock


@pytest.fixture
def mock_create_file_checklist():
    """Mock the create_file_checklist function."""
    with patch(
        "services.webhook.utils.create_pr_checkbox_comment.create_file_checklist"
    ) as mock:
        yield mock


@pytest.fixture
def mock_create_test_selection_comment():
    """Mock the create_test_selection_comment function."""
    with patch(
        "services.webhook.utils.create_pr_checkbox_comment.create_test_selection_comment"
    ) as mock:
        mock.return_value = "mock_comment"
        yield mock


@pytest.fixture
def mock_delete_comments_by_identifiers():
    """Mock the delete_comments_by_identifiers function."""
    with patch(
        "services.webhook.utils.create_pr_checkbox_comment.delete_comments_by_identifiers"
    ) as mock:
        yield mock


@pytest.fixture
def mock_combine_and_create_comment():
    """Mock the combine_and_create_comment function."""
    with patch(
        "services.webhook.utils.create_pr_checkbox_comment.combine_and_create_comment"
    ) as mock:
        yield mock


@pytest.fixture
def mock_logging():
    """Mock the logging module."""
    with patch("services.webhook.utils.create_pr_checkbox_comment.logging") as mock:
        yield mock


@pytest.fixture
def all_mocks(
    mock_get_repository,
    mock_get_installation_access_token,
    mock_get_pull_request_files,
    mock_is_code_file,
    mock_is_test_file,
    mock_is_type_file,
    mock_get_coverages,
    mock_create_file_checklist,
    mock_create_test_selection_comment,
    mock_delete_comments_by_identifiers,
    mock_combine_and_create_comment,
    mock_logging,
):
    """Fixture that provides all mocks."""
    return {
        "get_repository": mock_get_repository,
        "get_installation_access_token": mock_get_installation_access_token,
        "get_pull_request_files": mock_get_pull_request_files,
        "is_code_file": mock_is_code_file,
        "is_test_file": mock_is_test_file,
        "is_type_file": mock_is_type_file,
        "get_coverages": mock_get_coverages,
        "create_file_checklist": mock_create_file_checklist,
        "create_test_selection_comment": mock_create_test_selection_comment,
        "delete_comments_by_identifiers": mock_delete_comments_by_identifiers,
        "combine_and_create_comment": mock_combine_and_create_comment,
        "logging": mock_logging,
    }


class TestCreatePrCheckboxComment:
    """Test cases for create_pr_checkbox_comment function."""

    def test_skips_bot_sender(self, all_mocks):
        """Test that the function skips processing when sender is a bot."""
        # Arrange
        payload = create_mock_payload(sender_login="dependabot[bot]")

        # Act
        result = create_pr_checkbox_comment(payload)

        # Assert
        assert result is None
        all_mocks["logging"].info.assert_called_once_with(
            "Skipping PR test selection for bot dependabot[bot]"
        )
        all_mocks["get_repository"].assert_not_called()

    def test_skips_when_repository_not_found(self, all_mocks):
        """Test that the function skips processing when repository is not found."""
        # Arrange
        payload = create_mock_payload()
        all_mocks["get_repository"].return_value = None

        # Act
        result = create_pr_checkbox_comment(payload)

        # Assert
        assert result is None
        all_mocks["logging"].info.assert_called_once_with(
            "Skipping PR test selection for repo test-repo because trigger_on_pr_change is False"
        )
        all_mocks["get_repository"].assert_called_once_with(repo_id=123)

    def test_skips_when_trigger_on_pr_change_is_false(self, all_mocks):
        """Test that the function skips processing when trigger_on_pr_change is False."""
        # Arrange
        payload = create_mock_payload()
        all_mocks["get_repository"].return_value = create_mock_repository(
            trigger_on_pr_change=False
        )

        # Act
        result = create_pr_checkbox_comment(payload)

        # Assert
        assert result is None
        all_mocks["logging"].info.assert_called_once_with(
            "Skipping PR test selection for repo test-repo because trigger_on_pr_change is False"
        )

    def test_skips_when_no_code_files_changed(self, all_mocks):
        """Test that the function skips processing when no code files are changed."""
        # Arrange
        payload = create_mock_payload()
        all_mocks["get_repository"].return_value = create_mock_repository()
        all_mocks["get_pull_request_files"].return_value = [
            create_file_change("test_file.py", "modified"),
            create_file_change("types.py", "added"),
        ]
        all_mocks["is_code_file"].return_value = True
        all_mocks["is_test_file"].side_effect = lambda f: f == "test_file.py"
        all_mocks["is_type_file"].side_effect = lambda f: f == "types.py"

        # Act
        result = create_pr_checkbox_comment(payload)

        # Assert
        assert result is None
        all_mocks["logging"].info.assert_called_once_with(
            "Skipping PR test selection for repo test-repo because no code files were changed"
        )

    def test_successful_comment_creation(self, all_mocks):
        """Test successful comment creation with valid code files."""
        # Arrange
        payload = create_mock_payload()
        all_mocks["get_repository"].return_value = create_mock_repository()
        all_mocks["get_pull_request_files"].return_value = [
            create_file_change("src/main.py", "modified"),
            create_file_change("src/utils.py", "added"),
        ]
        all_mocks["is_code_file"].return_value = True
        all_mocks["is_test_file"].return_value = False
        all_mocks["is_type_file"].return_value = False
        all_mocks["get_coverages"].return_value = {
            "src/main.py": create_coverage_data("src/main.py", line_coverage=80.0)
        }
        all_mocks["create_file_checklist"].return_value = [
            {
                "path": "src/main.py",
                "checked": True,
                "status": "modified",
                "coverage_info": " (Line: 80.0%)",
            }
        ]

        # Act
        result = create_pr_checkbox_comment(payload)

        # Assert
        assert result is None  # Function returns None on success
        all_mocks["get_installation_access_token"].assert_called_once_with(
            installation_id=789
        )
        all_mocks["get_pull_request_files"].assert_called_once_with(
            url="https://api.github.com/repos/testowner/test-repo/pulls/1/files",
            token="mock_token",
        )
        all_mocks["get_coverages"].assert_called_once_with(
            repo_id=123, filenames=["src/main.py", "src/utils.py"]
        )
        all_mocks["create_test_selection_comment"].assert_called_once()
        all_mocks["delete_comments_by_identifiers"].assert_called_once()
        all_mocks["combine_and_create_comment"].assert_called_once()

    def test_file_filtering_logic(self, all_mocks):
        """Test that files are correctly filtered based on type."""
        # Arrange
        payload = create_mock_payload()
        all_mocks["get_repository"].return_value = create_mock_repository()
        all_mocks["get_pull_request_files"].return_value = [
            create_file_change("src/main.py", "modified"),  # Code file
            create_file_change("test_main.py", "added"),  # Test file
            create_file_change("types.py", "modified"),  # Type file
            create_file_change("README.md", "modified"),  # Not a code file
            create_file_change("src/utils.py", "added"),  # Code file
        ]

        def mock_is_code_file(filename):
            return filename.endswith(".py")

        def mock_is_test_file(filename):
            return filename.startswith("test_")

        def mock_is_type_file(filename):
            return filename == "types.py"

        all_mocks["is_code_file"].side_effect = mock_is_code_file
        all_mocks["is_test_file"].side_effect = mock_is_test_file
        all_mocks["is_type_file"].side_effect = mock_is_type_file
        all_mocks["get_coverages"].return_value = {}
        all_mocks["create_file_checklist"].return_value = []

        # Act
        create_pr_checkbox_comment(payload)

        # Assert
        # Should only pass code files that are not test files or type files
        all_mocks["get_coverages"].assert_called_once_with(
            repo_id=123, filenames=["src/main.py", "src/utils.py"]
        )

    def test_comment_creation_with_branch_name(self, all_mocks):
        """Test that branch name is correctly passed to comment creation."""
        # Arrange
        payload = create_mock_payload(branch_name="feature/new-feature")
        all_mocks["get_repository"].return_value = create_mock_repository()
        all_mocks["get_pull_request_files"].return_value = [
            create_file_change("src/main.py", "modified")
        ]
        all_mocks["is_code_file"].return_value = True
        all_mocks["is_test_file"].return_value = False
        all_mocks["is_type_file"].return_value = False
        all_mocks["get_coverages"].return_value = {}
        all_mocks["create_file_checklist"].return_value = []

        # Act
        create_pr_checkbox_comment(payload)

        # Assert
        all_mocks["create_test_selection_comment"].assert_called_once_with(
            [], "feature/new-feature"
        )

    def test_delete_comments_called_with_correct_identifier(self, all_mocks):
        """Test that delete_comments_by_identifiers is called with correct parameters."""
        # Arrange
        payload = create_mock_payload()
        all_mocks["get_repository"].return_value = create_mock_repository()
        all_mocks["get_pull_request_files"].return_value = [
            create_file_change("src/main.py", "modified")
        ]
        all_mocks["is_code_file"].return_value = True
        all_mocks["is_test_file"].return_value = False
        all_mocks["is_type_file"].return_value = False
        all_mocks["get_coverages"].return_value = {}
        all_mocks["create_file_checklist"].return_value = []

        # Act
        create_pr_checkbox_comment(payload)

        # Assert
        expected_base_args = {
            "owner": "testowner",
            "repo": "test-repo",
            "issue_number": 1,
            "token": "mock_token",
        }
        all_mocks["delete_comments_by_identifiers"].assert_called_once_with(
            base_args=expected_base_args, identifiers=["## 🧪 Manage Tests?"]
        )

    def test_combine_and_create_comment_called_with_correct_parameters(self, all_mocks):
        """Test that combine_and_create_comment is called with correct parameters."""
        # Arrange
        payload = create_mock_payload(
            sender_login="testuser",
            owner_id=456,
            owner_login="testowner",
            installation_id=789,
        )
        all_mocks["get_repository"].return_value = create_mock_repository()
        all_mocks["get_pull_request_files"].return_value = [
            create_file_change("src/main.py", "modified")
        ]
        all_mocks["is_code_file"].return_value = True
        all_mocks["is_test_file"].return_value = False
        all_mocks["is_type_file"].return_value = False
        all_mocks["get_coverages"].return_value = {}
        all_mocks["create_file_checklist"].return_value = []

        # Act
        create_pr_checkbox_comment(payload)

        # Assert
        expected_base_args = {
            "owner": "testowner",
            "repo": "test-repo",
            "issue_number": 1,
            "token": "mock_token",
        }
        all_mocks["combine_and_create_comment"].assert_called_once_with(
            base_comment="mock_comment",
            installation_id=789,
            owner_id=456,
            owner_name="testowner",
            sender_name="testuser",
            base_args=expected_base_args,
        )

    def test_handles_empty_coverage_data(self, all_mocks):
        """Test that the function handles empty coverage data correctly."""
        # Arrange
        payload = create_mock_payload()
        all_mocks["get_repository"].return_value = create_mock_repository()
        all_mocks["get_pull_request_files"].return_value = [
            create_file_change("src/main.py", "modified")
        ]
        all_mocks["is_code_file"].return_value = True
        all_mocks["is_test_file"].return_value = False
        all_mocks["is_type_file"].return_value = False
        all_mocks["get_coverages"].return_value = {}
        all_mocks["create_file_checklist"].return_value = [
            {"path": "src/main.py", "checked": True, "status": "modified", "coverage_info": ""}
        ]

        # Act
        result = create_pr_checkbox_comment(payload)

        # Assert
        assert result is None
        all_mocks["create_file_checklist"].assert_called_once_with(
            [create_file_change("src/main.py", "modified")], {}
        )

    def test_handles_multiple_file_types(self, all_mocks):
        """Test that the function correctly handles multiple file types and statuses."""
        # Arrange
        payload = create_mock_payload()
        all_mocks["get_repository"].return_value = create_mock_repository()
        all_mocks["get_pull_request_files"].return_value = [
            create_file_change("src/main.py", "modified"),
            create_file_change("src/utils.py", "added"),
            create_file_change("src/old.py", "removed"),
        ]
        all_mocks["is_code_file"].return_value = True
        all_mocks["is_test_file"].return_value = False
        all_mocks["is_type_file"].return_value = False
        all_mocks["get_coverages"].return_value = {
            "src/main.py": create_coverage_data("src/main.py", line_coverage=75.0),
            "src/utils.py": create_coverage_data("src/utils.py", line_coverage=90.0),
        }
        all_mocks["create_file_checklist"].return_value = [
            {"path": "src/main.py", "checked": True, "status": "modified", "coverage_info": " (Line: 75.0%)"},
            {"path": "src/utils.py", "checked": True, "status": "added", "coverage_info": " (Line: 90.0%)"},
            {"path": "src/old.py", "checked": True, "status": "removed", "coverage_info": ""},
        ]

        # Act
        result = create_pr_checkbox_comment(payload)

        # Assert
        assert result is None
        all_mocks["get_coverages"].assert_called_once_with(
            repo_id=123, filenames=["src/main.py", "src/utils.py", "src/old.py"]
        )

    def test_bot_detection_with_different_bot_names(self, all_mocks):
        """Test that different bot names are correctly detected."""
        bot_names = [
            "dependabot[bot]",
            "github-actions[bot]",
            "renovate[bot]",
            "gitauto-ai[bot]",
            "custom-bot[bot]",
        ]

        for bot_name in bot_names:
            # Arrange
            payload = create_mock_payload(sender_login=bot_name)
            all_mocks["logging"].reset_mock()

            # Act
            result = create_pr_checkbox_comment(payload)

            # Assert
            assert result is None
            all_mocks["logging"].info.assert_called_once_with(
                f"Skipping PR test selection for bot {bot_name}"
            )

    def test_non_bot_user_is_processed(self, all_mocks):
        """Test that non-bot users are processed normally."""
        # Arrange
        payload = create_mock_payload(sender_login="regular-user")
        all_mocks["get_repository"].return_value = create_mock_repository()
        all_mocks["get_pull_request_files"].return_value = [
            create_file_change("src/main.py", "modified")
        ]
        all_mocks["is_code_file"].return_value = True
        all_mocks["is_test_file"].return_value = False
        all_mocks["is_type_file"].return_value = False
        all_mocks["get_coverages"].return_value = {}
        all_mocks["create_file_checklist"].return_value = []

        # Act
        result = create_pr_checkbox_comment(payload)

        # Assert
        assert result is None
        all_mocks["get_repository"].assert_called_once()
        # Should not log bot skip message
        bot_skip_calls = [
            call for call in all_mocks["logging"].info.call_args_list
            if "bot" in str(call)
        ]
        assert len(bot_skip_calls) == 0

    def test_handles_exception_gracefully(self, all_mocks):
        """Test that the function handles exceptions gracefully due to @handle_exceptions decorator."""
        # Arrange
        payload = create_mock_payload()
        all_mocks["get_repository"].side_effect = Exception("Database error")

        # Act
        result = create_pr_checkbox_comment(payload)

        # Assert
        # Due to @handle_exceptions decorator, should return None instead of raising
        assert result is None

    def test_pull_request_url_construction(self, all_mocks):
        """Test that pull request files URL is correctly constructed."""
        # Arrange
        payload = create_mock_payload(
            pull_url="https://api.github.com/repos/owner/repo/pulls/42"
        )
        all_mocks["get_repository"].return_value = create_mock_repository()
        all_mocks["get_pull_request_files"].return_value = [
            create_file_change("src/main.py", "modified")
        ]
        all_mocks["is_code_file"].return_value = True
        all_mocks["is_test_file"].return_value = False
        all_mocks["is_type_file"].return_value = False
        all_mocks["get_coverages"].return_value = {}
        all_mocks["create_file_checklist"].return_value = []

        # Act
        create_pr_checkbox_comment(payload)

        # Assert
        all_mocks["get_pull_request_files"].assert_called_once_with(
            url="https://api.github.com/repos/owner/repo/pulls/42/files",
            token="mock_token",
        )

    def test_coverage_data_passed_correctly(self, all_mocks):
        """Test that coverage data is correctly passed to create_file_checklist."""
        # Arrange
        payload = create_mock_payload()
        all_mocks["get_repository"].return_value = create_mock_repository()
        all_mocks["get_pull_request_files"].return_value = [
            create_file_change("src/main.py", "modified"),
            create_file_change("src/utils.py", "added"),
        ]
        all_mocks["is_code_file"].return_value = True
        all_mocks["is_test_file"].return_value = False
        all_mocks["is_type_file"].return_value = False

        expected_coverage_data = {
            "src/main.py": create_coverage_data("src/main.py", line_coverage=80.0),
            "src/utils.py": create_coverage_data("src/utils.py", line_coverage=60.0),
        }
        all_mocks["get_coverages"].return_value = expected_coverage_data
        all_mocks["create_file_checklist"].return_value = []

        # Act
        create_pr_checkbox_comment(payload)

        # Assert
        all_mocks["create_file_checklist"].assert_called_once_with(
            [
                create_file_change("src/main.py", "modified"),
                create_file_change("src/utils.py", "added"),
            ],
            expected_coverage_data,
        )

    def test_integration_with_real_dependencies(self):
        """Test the function with minimal mocking to verify integration."""
        # Arrange
        payload = create_mock_payload(sender_login="testbot[bot]")

        # Act
        result = create_pr_checkbox_comment(payload)

        # Assert
        # Should skip due to bot detection without needing other dependencies
        assert result is None

    def test_empty_file_changes_list(self, all_mocks):
        """Test behavior when get_pull_request_files returns empty list."""
        # Arrange
        payload = create_mock_payload()
        all_mocks["get_repository"].return_value = create_mock_repository()
        all_mocks["get_pull_request_files"].return_value = []

        # Act
        result = create_pr_checkbox_comment(payload)

        # Assert
        assert result is None
        all_mocks["logging"].info.assert_called_once_with(
            "Skipping PR test selection for repo test-repo because no code files were changed"
        )

    def test_all_files_filtered_out(self, all_mocks):
        """Test behavior when all files are filtered out (test files, type files, or non-code files)."""
        # Arrange
        payload = create_mock_payload()
        all_mocks["get_repository"].return_value = create_mock_repository()
        all_mocks["get_pull_request_files"].return_value = [
            create_file_change("test_main.py", "modified"),
            create_file_change("types.py", "added"),
            create_file_change("README.md", "modified"),
        ]
        all_mocks["is_code_file"].side_effect = lambda f: f.endswith(".py")
        all_mocks["is_test_file"].side_effect = lambda f: f.startswith("test_")
        all_mocks["is_type_file"].side_effect = lambda f: f == "types.py"

        # Act
        result = create_pr_checkbox_comment(payload)

        # Assert
        assert result is None
        all_mocks["logging"].info.assert_called_once_with(
            "Skipping PR test selection for repo test-repo because no code files were changed"
        )

    def test_mixed_file_types_only_code_files_processed(self, all_mocks):
        """Test that only valid code files are processed when mixed with other file types."""
        # Arrange
        payload = create_mock_payload()
        all_mocks["get_repository"].return_value = create_mock_repository()
        all_mocks["get_pull_request_files"].return_value = [
            create_file_change("src/main.py", "modified"),  # Valid code file
            create_file_change("test_main.py", "added"),  # Test file - should be filtered
            create_file_change("types.py", "modified"),  # Type file - should be filtered
            create_file_change("README.md", "modified"),  # Non-code file - should be filtered
            create_file_change("src/utils.py", "added"),  # Valid code file
        ]
        all_mocks["is_code_file"].side_effect = lambda f: f.endswith(".py")
        all_mocks["is_test_file"].side_effect = lambda f: f.startswith("test_")
        all_mocks["is_type_file"].side_effect = lambda f: f == "types.py"
        all_mocks["get_coverages"].return_value = {}
        all_mocks["create_file_checklist"].return_value = []

        # Act
        create_pr_checkbox_comment(payload)

        # Assert
        # Only the valid code files should be passed to get_coverages
        all_mocks["get_coverages"].assert_called_once_with(
            repo_id=123, filenames=["src/main.py", "src/utils.py"]
        )

    def test_repository_id_extraction(self, all_mocks):
        """Test that repository ID is correctly extracted from payload."""
        # Arrange
        payload = create_mock_payload(repo_id=999)
        all_mocks["get_repository"].return_value = create_mock_repository(repo_id=999)
        all_mocks["get_pull_request_files"].return_value = [
            create_file_change("src/main.py", "modified")
        ]
        all_mocks["is_code_file"].return_value = True
        all_mocks["is_test_file"].return_value = False
        all_mocks["is_type_file"].return_value = False
        all_mocks["get_coverages"].return_value = {}
        all_mocks["create_file_checklist"].return_value = []

        # Act
        create_pr_checkbox_comment(payload)

        # Assert
        all_mocks["get_repository"].assert_called_once_with(repo_id=999)
        all_mocks["get_coverages"].assert_called_once_with(
            repo_id=999, filenames=["src/main.py"]
        )

    def test_installation_id_extraction(self, all_mocks):
        """Test that installation ID is correctly extracted and used."""
        # Arrange
        payload = create_mock_payload(installation_id=12345)
        all_mocks["get_repository"].return_value = create_mock_repository()
        all_mocks["get_pull_request_files"].return_value = [
            create_file_change("src/main.py", "modified")
        ]
        all_mocks["is_code_file"].return_value = True
        all_mocks["is_test_file"].return_value = False
        all_mocks["is_type_file"].return_value = False
        all_mocks["get_coverages"].return_value = {}
        all_mocks["create_file_checklist"].return_value = []

        # Act
        create_pr_checkbox_comment(payload)

        # Assert
        all_mocks["get_installation_access_token"].assert_called_once_with(
            installation_id=12345
        )
        all_mocks["combine_and_create_comment"].assert_called_once()
        call_args = all_mocks["combine_and_create_comment"].call_args
        assert call_args[1]["installation_id"] == 12345

    def test_complex_scenario_with_all_components(self, all_mocks):
        """Test a complex scenario that exercises all major code paths."""
        # Arrange
        payload = create_mock_payload(
            sender_login="developer",
            repo_id=555,
            repo_name="complex-repo",
            owner_id=777,
            owner_login="complex-owner",
            pull_number=99,
            installation_id=888,
            branch_name="feature/complex-feature",
        )
        all_mocks["get_repository"].return_value = create_mock_repository(
            repo_id=555, trigger_on_pr_change=True
        )
        all_mocks["get_pull_request_files"].return_value = [
            create_file_change("src/main.py", "modified"),
            create_file_change("src/utils.py", "added"),
            create_file_change("src/old_feature.py", "removed"),
            create_file_change("test_main.py", "modified"),  # Should be filtered
            create_file_change("types.py", "added"),  # Should be filtered
        ]
        all_mocks["is_code_file"].side_effect = lambda f: f.endswith(".py")
        all_mocks["is_test_file"].side_effect = lambda f: f.startswith("test_")
        all_mocks["is_type_file"].side_effect = lambda f: f == "types.py"

        coverage_data = {
            "src/main.py": create_coverage_data("src/main.py", line_coverage=85.0),
            "src/utils.py": create_coverage_data("src/utils.py", line_coverage=92.0),
        }
        all_mocks["get_coverages"].return_value = coverage_data

        checklist = [
            {"path": "src/main.py", "checked": True, "status": "modified", "coverage_info": " (Line: 85.0%)"},
            {"path": "src/utils.py", "checked": True, "status": "added", "coverage_info": " (Line: 92.0%)"},
            {"path": "src/old_feature.py", "checked": True, "status": "removed", "coverage_info": ""},
        ]
        all_mocks["create_file_checklist"].return_value = checklist

        # Act
        result = create_pr_checkbox_comment(payload)

        # Assert
        assert result is None

        # Verify all major function calls
        all_mocks["get_repository"].assert_called_once_with(repo_id=555)
        all_mocks["get_installation_access_token"].assert_called_once_with(installation_id=888)
        all_mocks["get_coverages"].assert_called_once_with(
            repo_id=555, filenames=["src/main.py", "src/utils.py", "src/old_feature.py"]
        )
        all_mocks["create_file_checklist"].assert_called_once_with(
            [
                create_file_change("src/main.py", "modified"),
                create_file_change("src/utils.py", "added"),
                create_file_change("src/old_feature.py", "removed"),
            ],
            coverage_data,
        )
        all_mocks["create_test_selection_comment"].assert_called_once_with(
            checklist, "feature/complex-feature"
        )

        expected_base_args = {
            "owner": "complex-owner",
            "repo": "complex-repo",
            "issue_number": 99,
            "token": "mock_token",
        }
        all_mocks["delete_comments_by_identifiers"].assert_called_once_with(
            base_args=expected_base_args, identifiers=["## 🧪 Manage Tests?"]
        )
        all_mocks["combine_and_create_comment"].assert_called_once_with(
            base_comment="mock_comment",
            installation_id=888,
            owner_id=777,
            owner_name="complex-owner",
            sender_name="developer",
            base_args=expected_base_args,
        )
