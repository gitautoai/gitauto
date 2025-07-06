import pytest
from unittest.mock import patch, MagicMock

from services.webhook.utils.create_pr_checkbox_comment import create_pr_checkbox_comment


@pytest.fixture
def mock_dependencies():
    """Mock all external dependencies."""
    mocks = {}
    
    with patch("services.webhook.utils.create_pr_checkbox_comment.get_installation_access_token") as mock_token:
        mock_token.return_value = "mock_token"
        mocks["get_installation_access_token"] = mock_token
        
        with patch("services.webhook.utils.create_pr_checkbox_comment.get_repository") as mock_repo:
            mock_repo.return_value = {"trigger_on_pr_change": True}
            mocks["get_repository"] = mock_repo
            
            with patch("services.webhook.utils.create_pr_checkbox_comment.get_pull_request_files") as mock_files:
                mock_files.return_value = []
                mocks["get_pull_request_files"] = mock_files
                
                with patch("services.webhook.utils.create_pr_checkbox_comment.is_code_file") as mock_code:
                    mock_code.return_value = True
                    mocks["is_code_file"] = mock_code
                    
                    with patch("services.webhook.utils.create_pr_checkbox_comment.is_test_file") as mock_test:
                        mock_test.return_value = False
                        mocks["is_test_file"] = mock_test
                        
                        with patch("services.webhook.utils.create_pr_checkbox_comment.is_type_file") as mock_type:
                            mock_type.return_value = False
                            mocks["is_type_file"] = mock_type
                            
                            with patch("services.webhook.utils.create_pr_checkbox_comment.get_coverages") as mock_cov:
                                mock_cov.return_value = {}
                                mocks["get_coverages"] = mock_cov
                                
                                with patch("services.webhook.utils.create_pr_checkbox_comment.create_file_checklist") as mock_checklist:
                                    mock_checklist.return_value = []
                                    mocks["create_file_checklist"] = mock_checklist
                                    
                                    with patch("services.webhook.utils.create_pr_checkbox_comment.create_test_selection_comment") as mock_comment:
                                        mock_comment.return_value = "mock_comment"
                                        mocks["create_test_selection_comment"] = mock_comment
                                        
                                        with patch("services.webhook.utils.create_pr_checkbox_comment.delete_comments_by_identifiers") as mock_delete:
                                            mocks["delete_comments_by_identifiers"] = mock_delete
                                            
                                            with patch("services.webhook.utils.create_pr_checkbox_comment.combine_and_create_comment") as mock_combine:
                                                mocks["combine_and_create_comment"] = mock_combine
                                                
                                                yield mocks


@pytest.fixture
def sample_payload():
    """Sample PR webhook payload for testing."""
    return {
        "pull_request": {
            "number": 123,
            "url": "https://api.github.com/repos/owner/repo/pulls/123",
            "head": {"ref": "feature-branch"},
        },
        "sender": {"login": "test-user"},
        "repository": {
            "id": 456,
            "name": "test-repo",
            "owner": {
                "id": 789,
                "type": "Organization",
                "login": "test-owner",
            },
        },
        "installation": {"id": 101112},
    }


@pytest.fixture
def bot_payload(sample_payload):
    """Sample payload from a bot user."""
    payload = sample_payload.copy()
    payload["sender"]["login"] = "dependabot[bot]"
    return payload


@pytest.fixture
def disabled_repo_payload(sample_payload):
    """Sample payload for a repository with PR test selection disabled."""
    return sample_payload


class TestCreatePrCheckboxComment:
    """Test cases for create_pr_checkbox_comment function."""

    def test_skips_bot_users(self, mock_dependencies, bot_payload):
        """Test that the function skips processing for bot users."""
        result = create_pr_checkbox_comment(bot_payload)
        
        assert result is None
        # Verify that no further processing was done
        mock_dependencies["get_repository"].assert_not_called()

    def test_skips_when_trigger_disabled(self, mock_dependencies, sample_payload):
        """Test that the function skips processing when trigger_on_pr_change is disabled."""
        mock_dependencies["get_repository"].return_value = {"trigger_on_pr_change": False}
        
        result = create_pr_checkbox_comment(sample_payload)
        
        assert result is None
        mock_dependencies["get_repository"].assert_called_once_with(repo_id=456)
        # Verify that no further processing was done
        mock_dependencies["get_installation_access_token"].assert_not_called()

    def test_skips_when_no_repo_settings(self, mock_dependencies, sample_payload):
        """Test that the function skips processing when repository settings are not found."""
        mock_dependencies["get_repository"].return_value = None
        
        result = create_pr_checkbox_comment(sample_payload)
        
        assert result is None
        mock_dependencies["get_repository"].assert_called_once_with(repo_id=456)

    def test_skips_when_no_code_files_changed(self, mock_dependencies, sample_payload):
        """Test that the function skips processing when no code files were changed."""
        mock_dependencies["get_pull_request_files"].return_value = [
            {"filename": "README.md", "status": "modified"},
            {"filename": "docs/guide.txt", "status": "added"},
        ]
        mock_dependencies["is_code_file"].return_value = False
        
        result = create_pr_checkbox_comment(sample_payload)
        
        assert result is None
        # Verify that coverage data was not fetched
        mock_dependencies["get_coverages"].assert_not_called()

    def test_skips_test_files(self, mock_dependencies, sample_payload):
        """Test that the function filters out test files."""
        mock_dependencies["get_pull_request_files"].return_value = [
            {"filename": "src/main.py", "status": "modified"},
            {"filename": "tests/test_main.py", "status": "modified"},
        ]
        mock_dependencies["is_code_file"].return_value = True
        mock_dependencies["is_test_file"].side_effect = lambda f: f.startswith("tests/")
        
        create_pr_checkbox_comment(sample_payload)
        
        # Verify that only non-test files were processed
        mock_dependencies["get_coverages"].assert_called_once_with(
            repo_id=456, filenames=["src/main.py"]
        )

    def test_skips_type_files(self, mock_dependencies, sample_payload):
        """Test that the function filters out type files."""
        mock_dependencies["get_pull_request_files"].return_value = [
            {"filename": "src/main.py", "status": "modified"},
            {"filename": "src/types.py", "status": "modified"},
        ]
        mock_dependencies["is_code_file"].return_value = True
        mock_dependencies["is_test_file"].return_value = False
        mock_dependencies["is_type_file"].side_effect = lambda f: f.endswith("types.py")
        
        create_pr_checkbox_comment(sample_payload)
        
        # Verify that only non-type files were processed
        mock_dependencies["get_coverages"].assert_called_once_with(
            repo_id=456, filenames=["src/main.py"]
        )

    def test_successful_comment_creation(self, mock_dependencies, sample_payload):
        """Test successful comment creation with code files."""
        mock_dependencies["get_pull_request_files"].return_value = [
            {"filename": "src/main.py", "status": "modified"},
            {"filename": "src/utils.py", "status": "added"},
        ]
        mock_dependencies["create_file_checklist"].return_value = [
            {
                "path": "src/main.py",
                "checked": True,
                "coverage_info": " (Coverage: 75%)",
                "status": "modified",
            },
            {
                "path": "src/utils.py",
                "checked": True,
                "coverage_info": "",
                "status": "added",
            },
        ]
        
        create_pr_checkbox_comment(sample_payload)
        
        # Verify the complete flow was executed
        mock_dependencies["get_installation_access_token"].assert_called_once_with(
            installation_id=101112
        )
        mock_dependencies["get_pull_request_files"].assert_called_once_with(
            url="https://api.github.com/repos/owner/repo/pulls/123/files",
            token="mock_token"
        )
        mock_dependencies["get_coverages"].assert_called_once_with(
            repo_id=456, filenames=["src/main.py", "src/utils.py"]
        )
        mock_dependencies["create_file_checklist"].assert_called_once()
        mock_dependencies["create_test_selection_comment"].assert_called_once()
        mock_dependencies["delete_comments_by_identifiers"].assert_called_once()
        mock_dependencies["combine_and_create_comment"].assert_called_once()

    def test_delete_existing_comments(self, mock_dependencies, sample_payload):
        """Test that existing test selection comments are deleted."""
        mock_dependencies["get_pull_request_files"].return_value = [
            {"filename": "src/main.py", "status": "modified"}
        ]
        
        create_pr_checkbox_comment(sample_payload)
        
        # Verify that existing comments are deleted
        mock_dependencies["delete_comments_by_identifiers"].assert_called_once()
        call_args = mock_dependencies["delete_comments_by_identifiers"].call_args
        assert "base_args" in call_args.kwargs
        assert "identifiers" in call_args.kwargs

    def test_combine_and_create_comment_called_with_correct_args(self, mock_dependencies, sample_payload):
        """Test that combine_and_create_comment is called with correct arguments."""
        mock_dependencies["get_pull_request_files"].return_value = [
            {"filename": "src/main.py", "status": "modified"}
        ]
        
        create_pr_checkbox_comment(sample_payload)
        
        # Verify combine_and_create_comment was called with expected arguments
        mock_dependencies["combine_and_create_comment"].assert_called_once()
        call_args = mock_dependencies["combine_and_create_comment"].call_args
        
        assert call_args.kwargs["base_comment"] == "mock_comment"
        assert call_args.kwargs["installation_id"] == 101112
        assert call_args.kwargs["owner_id"] == 789
        assert call_args.kwargs["owner_name"] == "test-owner"
        assert call_args.kwargs["owner_type"] == "Organization"
        assert call_args.kwargs["repo_name"] == "test-repo"
        assert call_args.kwargs["issue_number"] == 123
        assert call_args.kwargs["sender_name"] == "test-user"

    def test_base_args_construction(self, mock_dependencies, sample_payload):
        """Test that base_args are constructed correctly."""
        mock_dependencies["get_pull_request_files"].return_value = [
            {"filename": "src/main.py", "status": "modified"}
        ]
        
        create_pr_checkbox_comment(sample_payload)
        
        # Check that delete_comments_by_identifiers was called with correct base_args
        call_args = mock_dependencies["delete_comments_by_identifiers"].call_args
        base_args = call_args.kwargs["base_args"]
        
        assert base_args["owner"] == "test-owner"
        assert base_args["repo"] == "test-repo"
        assert base_args["issue_number"] == 123
        assert base_args["token"] == "mock_token"

    def test_branch_name_extraction(self, mock_dependencies, sample_payload):
        """Test that branch name is correctly extracted and passed."""
        mock_dependencies["get_pull_request_files"].return_value = [
            {"filename": "src/main.py", "status": "modified"}
        ]
        
        create_pr_checkbox_comment(sample_payload)
        
        # Verify that create_test_selection_comment was called with the correct branch name
        mock_dependencies["create_test_selection_comment"].assert_called_once()
        call_args = mock_dependencies["create_test_selection_comment"].call_args
        assert call_args[0][1] == "feature-branch"  # Second argument should be branch name

    def test_handles_empty_file_list_after_filtering(self, mock_dependencies, sample_payload):
        """Test handling when all files are filtered out."""
        mock_dependencies["get_pull_request_files"].return_value = [
            {"filename": "tests/test_main.py", "status": "modified"},
            {"filename": "types/user.py", "status": "added"},
        ]
        mock_dependencies["is_code_file"].return_value = True
        mock_dependencies["is_test_file"].side_effect = lambda f: f.startswith("tests/")
        mock_dependencies["is_type_file"].side_effect = lambda f: f.startswith("types/")
        
        result = create_pr_checkbox_comment(sample_payload)
        
        assert result is None
        # Verify that coverage data was not fetched
        mock_dependencies["get_coverages"].assert_not_called()

    def test_error_handling_with_exception_decorator(self, mock_dependencies, sample_payload):
        """Test that the function handles exceptions gracefully due to the decorator."""
        mock_dependencies["get_repository"].side_effect = Exception("Database error")
        
        # Should not raise an exception due to @handle_exceptions decorator
        result = create_pr_checkbox_comment(sample_payload)
        
        # The decorator should return None on error
        assert result is None

    def test_different_bot_name_patterns(self, mock_dependencies, sample_payload):
        """Test that different bot name patterns are correctly identified."""
        bot_names = [
            "dependabot[bot]",
            "github-actions[bot]",
            "renovate[bot]",
            "codecov[bot]",
            "custom-bot[bot]",
        ]
        
        for bot_name in bot_names:
            payload = sample_payload.copy()
            payload["sender"]["login"] = bot_name
            
            result = create_pr_checkbox_comment(payload)
            
            assert result is None
            # Reset mocks for next iteration
            for mock in mock_dependencies.values():
                mock.reset_mock()

    def test_non_bot_users_are_processed(self, mock_dependencies, sample_payload):
        """Test that non-bot users are processed normally."""
        non_bot_names = [
            "regular-user",
            "developer123",
            "team-member",
            "contributor",
        ]
        
        mock_dependencies["get_pull_request_files"].return_value = [
            {"filename": "src/main.py", "status": "modified"}
        ]
        
        for user_name in non_bot_names:
            payload = sample_payload.copy()
            payload["sender"]["login"] = user_name
            
            create_pr_checkbox_comment(payload)
            
            # Verify that processing continued (repository was checked)
            mock_dependencies["get_repository"].assert_called()
            # Reset mocks for next iteration
            for mock in mock_dependencies.values():
                mock.reset_mock()